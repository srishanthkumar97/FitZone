import logging
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models import Attendance, Membership, User
from .attendance_helpers import attendance_streaks, serialize_attendance


attendance_blueprint = Blueprint("attendance", __name__, url_prefix="/api/attendance")
logger = logging.getLogger(__name__)


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _current_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def _member_for_request():
    user = _current_user()
    if user is None:
        return None, _error("The account for this token no longer exists.", 401)
    if user.role != "member":
        return None, _error("Member access is required.", 403)
    if not user.is_active:
        return None, _error("This member account is deactivated.", 403)
    return user, None


def _attendance_dates(user_id: int) -> list[date]:
    return db.session.scalars(
        db.select(Attendance.attendance_date).where(Attendance.user_id == user_id)
    ).all()


def _validated_filter(name: str, minimum: int, maximum: int):
    raw_value = request.args.get(name)
    if raw_value is None:
        return None, None
    try:
        value = int(raw_value)
    except ValueError:
        return None, _error(f"{name} must be a number.", 400)
    if not minimum <= value <= maximum:
        return None, _error(f"{name} must be between {minimum} and {maximum}.", 400)
    return value, None


@attendance_blueprint.post("/check-in")
@jwt_required()
def check_in():
    user, error = _member_for_request()
    if error:
        return error

    now = datetime.now()
    today = now.date()
    try:
        db.session.execute(
            update(Membership)
            .where(
                Membership.user_id == user.id,
                Membership.status == "active",
                Membership.end_date < today,
            )
            .values(status="expired")
        )
        active_membership = db.session.scalar(
            db.select(Membership.id).where(
                Membership.user_id == user.id,
                Membership.status == "active",
                Membership.start_date <= today,
                Membership.end_date >= today,
            )
        )
        if active_membership is None:
            latest_membership = db.session.scalar(
                db.select(Membership)
                .where(Membership.user_id == user.id)
                .order_by(Membership.end_date.desc(), Membership.id.desc())
            )
            db.session.commit()
            if latest_membership and (
                latest_membership.status == "expired"
                or latest_membership.end_date < today
            ):
                return _error(
                    "Your membership has expired. Please renew your membership.",
                    403,
                )
            if latest_membership and latest_membership.start_date > today:
                return _error("Your membership has not started yet.", 403)
            return _error("An active membership is required to check in.", 403)

        existing = db.session.scalar(
            db.select(Attendance.id).where(
                Attendance.user_id == user.id,
                Attendance.attendance_date == today,
            )
        )
        if existing is not None:
            db.session.commit()
            return _error("You have already checked in today.", 409)

        attendance = Attendance(
            user_id=user.id,
            attendance_date=today,
            check_in_time=now,
            status="checked_in",
        )
        db.session.add(attendance)
        db.session.flush()
        current_streak, _ = attendance_streaks(
            _attendance_dates(user.id),
            today,
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("You have already checked in today.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while checking in a member.")
        return _error("Unable to record attendance right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Check-in successful.",
            "attendance": serialize_attendance(attendance),
            "current_streak": current_streak,
        }
    ), 201


@attendance_blueprint.post("/check-out")
@jwt_required()
def check_out():
    user, error = _member_for_request()
    if error:
        return error

    try:
        attendance = db.session.scalar(
            db.select(Attendance)
            .where(
                Attendance.user_id == user.id,
                Attendance.attendance_date == date.today(),
            )
            .with_for_update()
        )
        if attendance is None:
            return _error("You must check in before checking out.", 404)
        if attendance.check_out_time is not None:
            return _error("You have already checked out today.", 409)

        attendance.check_out_time = datetime.now()
        attendance.status = "checked_out"
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while checking out a member.")
        return _error("Unable to record checkout right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Check-out successful.",
            "attendance": serialize_attendance(attendance),
        }
    ), 200


@attendance_blueprint.get("/history")
@jwt_required()
def get_history():
    user, error = _member_for_request()
    if error:
        return error

    month, error = _validated_filter("month", 1, 12)
    if error:
        return error
    year, error = _validated_filter("year", 1, 9999)
    if error:
        return error

    query = db.select(Attendance).where(Attendance.user_id == user.id)
    try:
        records = db.session.scalars(
            query.order_by(
                Attendance.attendance_date.desc(),
                Attendance.id.desc(),
            )
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving attendance history.")
        return _error("Unable to retrieve attendance history right now.", 503)

    if month is not None:
        records = [item for item in records if item.attendance_date.month == month]
    if year is not None:
        records = [item for item in records if item.attendance_date.year == year]

    return jsonify(
        {
            "success": True,
            "message": "Attendance history retrieved successfully.",
            "attendance": [serialize_attendance(item) for item in records],
        }
    ), 200


@attendance_blueprint.get("/summary")
@jwt_required()
def get_summary():
    user, error = _member_for_request()
    if error:
        return error

    today = date.today()
    month_start = today.replace(day=1)
    try:
        records = db.session.scalars(
            db.select(Attendance.attendance_date)
            .where(Attendance.user_id == user.id)
            .order_by(Attendance.attendance_date)
        ).all()
        total_days = len(records)
        current_month_days = sum(month_start <= attended_on <= today for attended_on in records)
        current_streak, longest_streak = attendance_streaks(records, today)
        last_attendance_date = max(
            (attended_on for attended_on in records if attended_on <= today),
            default=None,
        )
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving attendance summary.")
        return _error("Unable to retrieve attendance summary right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Attendance summary retrieved successfully.",
            "summary": {
                "total_attendance_days": total_days,
                "current_month_attendance": current_month_days,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "last_attendance_date": (
                    last_attendance_date.isoformat() if last_attendance_date else None
                ),
            },
        }
    ), 200
