import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Progress, User


progress_blueprint = Blueprint("progress", __name__, url_prefix="/api/progress")
logger = logging.getLogger(__name__)
PROGRESS_FIELDS = {
    "record_date",
    "weight",
    "height",
    "body_fat",
    "chest",
    "waist",
    "arms",
    "notes",
}
MEASUREMENT_FIELDS = {"weight", "height", "body_fat", "chest", "waist", "arms"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _member():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    user = db.session.get(User, user_id)
    return user if user and user.role == "member" and user.is_active else None


def _payload():
    if not request.is_json:
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _parse_decimal(value, field):
    if value is None:
        return None, None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None, f"{field} must be a valid number or null."
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, f"{field} must be a valid number or null."
    if not number.is_finite():
        return None, f"{field} must be a finite number."
    if field == "body_fat":
        valid = Decimal("0") <= number <= Decimal("100")
    else:
        valid = number > 0
    if not valid:
        return None, f"{field} is outside the valid range."
    if len(number.as_tuple().digits) > 8 or abs(number) >= Decimal("1000000"):
        return None, f"{field} is outside the supported range."
    return number, None


def _serialize_progress(record: Progress) -> dict:
    result = {
        "id": record.id,
        "user_id": record.user_id,
        "record_date": record.record_date.isoformat(),
        "notes": record.notes,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }
    result.update(
        {
            field: float(value) if value is not None else None
            for field in MEASUREMENT_FIELDS
            for value in [getattr(record, field)]
        }
    )
    return result


@progress_blueprint.post("")
@jwt_required()
def create_progress():
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if payload.keys() - PROGRESS_FIELDS:
        return _error("The progress record contains unsupported fields.", 400)
    if not payload.keys() & (MEASUREMENT_FIELDS | {"notes"}):
        return _error("Provide at least one measurement or notes.", 400)

    record_date_value = payload.get("record_date", date.today().isoformat())
    if not isinstance(record_date_value, str):
        return _error("record_date must use YYYY-MM-DD format.", 400)
    try:
        record_date = date.fromisoformat(record_date_value)
    except ValueError:
        return _error("record_date must use YYYY-MM-DD format.", 400)

    values = {}
    for field in MEASUREMENT_FIELDS & payload.keys():
        value, error = _parse_decimal(payload[field], field)
        if error:
            return _error(error, 400)
        values[field] = value

    notes = payload.get("notes")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 5000):
        return _error("notes must be a string of at most 5000 characters or null.", 400)
    if isinstance(notes, str):
        notes = notes.strip()

    record = Progress(
        user_id=user.id,
        record_date=record_date,
        notes=notes,
        **values,
    )
    db.session.add(record)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while creating a progress record.")
        return _error("Unable to save progress right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Progress record created successfully.",
            "progress": _serialize_progress(record),
        }
    ), 201


@progress_blueprint.get("")
@jwt_required()
def list_progress():
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    try:
        records = db.session.scalars(
            db.select(Progress)
            .where(Progress.user_id == user.id)
            .order_by(Progress.record_date.desc(), Progress.id.desc())
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving progress history.")
        return _error("Unable to retrieve progress right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Progress history retrieved successfully.",
            "progress": [_serialize_progress(item) for item in records],
        }
    ), 200


@progress_blueprint.get("/latest")
@jwt_required()
def get_latest_progress():
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    try:
        record = db.session.scalar(
            db.select(Progress)
            .where(Progress.user_id == user.id)
            .order_by(Progress.record_date.desc(), Progress.id.desc())
        )
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving latest progress.")
        return _error("Unable to retrieve progress right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Latest progress retrieved successfully.",
            "progress": _serialize_progress(record) if record else None,
        }
    ), 200
