import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Notification
from .admin_auth import admin_required


admin_announcement_blueprint = Blueprint(
    "admin_announcements",
    __name__,
    url_prefix="/api/admin/announcements",
)
logger = logging.getLogger(__name__)
FIELDS = {"title", "body", "is_active"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _payload():
    if not request.is_json:
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _validate(payload):
    if payload.keys() - FIELDS:
        return None, "Unsupported announcement fields."
    values = {}
    for key, maximum in (("title", 160), ("body", 10000)):
        if key not in payload:
            continue
        value = payload[key]
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            return None, f"{key} must be a non-empty string of at most {maximum} characters."
        values[key] = value.strip()
    if "is_active" in payload:
        if not isinstance(payload["is_active"], bool):
            return None, "is_active must be true or false."
        values["is_active"] = payload["is_active"]
    return values, None


def _serialize(item):
    return {
        "id": item.id,
        "title": item.title,
        "body": item.body,
        "is_active": item.is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@admin_announcement_blueprint.post("")
@admin_required
def create_announcement():
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not {"title", "body"} <= payload.keys():
        return _error("title and body are required.", 400)
    values, error = _validate(payload)
    if error:
        return _error(error, 400)
    try:
        admin_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return _error("The account for this token no longer exists.", 401)
    item = Notification(**values, created_by=admin_id)
    db.session.add(item)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while creating an announcement.")
        return _error("Unable to create the announcement right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Announcement created successfully.",
            "announcement": _serialize(item),
        }
    ), 201


@admin_announcement_blueprint.get("")
@admin_required
def list_announcements():
    try:
        items = db.session.scalars(
            db.select(Notification).order_by(Notification.created_at.desc(), Notification.id.desc())
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while listing announcements.")
        return _error("Unable to retrieve announcements right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Announcements retrieved successfully.",
            "announcements": [_serialize(item) for item in items],
        }
    ), 200


@admin_announcement_blueprint.put("/<int:announcement_id>")
@admin_required
def update_announcement(announcement_id: int):
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload:
        return _error("Provide at least one announcement field to update.", 400)
    values, error = _validate(payload)
    if error:
        return _error(error, 400)
    item = db.session.get(Notification, announcement_id)
    if item is None:
        return _error("Announcement not found.", 404)
    for key, value in values.items():
        setattr(item, key, value)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating an announcement.")
        return _error("Unable to update the announcement right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Announcement updated successfully.",
            "announcement": _serialize(item),
        }
    ), 200


@admin_announcement_blueprint.delete("/<int:announcement_id>")
@admin_required
def delete_announcement(announcement_id: int):
    item = db.session.get(Notification, announcement_id)
    if item is None:
        return _error("Announcement not found.", 404)
    try:
        db.session.delete(item)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while deleting an announcement.")
        return _error("Unable to delete the announcement right now.", 503)
    return jsonify({"success": True, "message": "Announcement deleted successfully."}), 200
