import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Attendance, User
from .admin_auth import admin_required
from .attendance_helpers import attendance_streaks, serialize_attendance


admin_attendance_blueprint = Blueprint(
    "admin_attendance",
    __name__,
    url_prefix="/api/admin/attendance",
)
logger = logging.getLogger(__name__)


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


@admin_attendance_blueprint.get("/today")
@admin_required
def get_today_attendance():
    today = date.today()
    try:
        records = db.session.scalars(
            db.select(Attendance)
            .where(Attendance.attendance_date == today)
            .order_by(Attendance.check_in_time)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving today's attendance.")
        return _error("Unable to retrieve attendance right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Today's attendance retrieved successfully.",
            "attendance": [serialize_attendance(item) for item in records],
        }
    ), 200


@admin_attendance_blueprint.get("/members/<int:user_id>")
@admin_attendance_blueprint.get("/member/<int:user_id>")
@admin_required
def get_member_attendance(user_id: int):
    try:
        member = db.session.get(User, user_id)
        if member is None or member.role != "member":
            return _error("Member account not found.", 404)
        records = db.session.scalars(
            db.select(Attendance)
            .where(Attendance.user_id == user_id)
            .order_by(Attendance.attendance_date.desc(), Attendance.id.desc())
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving member attendance.")
        return _error("Unable to retrieve member attendance right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Member attendance retrieved successfully.",
            "member": {"id": member.id, "name": member.name, "email": member.email},
            "attendance": [serialize_attendance(item) for item in records],
        }
    ), 200


@admin_attendance_blueprint.get("/statistics")
@admin_required
def get_attendance_statistics():
    today = date.today()
    month_start = today.replace(day=1)
    try:
        total_days = db.session.scalar(db.select(func.count(Attendance.id))) or 0
        today_count = db.session.scalar(
            db.select(func.count(Attendance.id)).where(
                Attendance.attendance_date == today
            )
        ) or 0
        month_count = db.session.scalar(
            db.select(func.count(Attendance.id)).where(
                Attendance.attendance_date >= month_start,
                Attendance.attendance_date <= today,
            )
        ) or 0
        today_members = db.session.scalar(
            db.select(func.count(func.distinct(Attendance.user_id))).where(
                Attendance.attendance_date == today
            )
        ) or 0
        dates_by_member = db.session.execute(
            db.select(Attendance.user_id, Attendance.attendance_date)
            .order_by(Attendance.user_id, Attendance.attendance_date)
        ).all()
        member_dates = {}
        for user_id, attendance_date in dates_by_member:
            member_dates.setdefault(user_id, []).append(attendance_date)
        longest_streak = max(
            (
                attendance_streaks(dates, today)[1]
                for dates in member_dates.values()
            ),
            default=0,
        )
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving attendance statistics.")
        return _error("Unable to retrieve attendance statistics right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Attendance statistics retrieved successfully.",
            "statistics": {
                "total_attendance_days": total_days,
                "today_attendance": today_count,
                "today_unique_members": today_members,
                "current_month_attendance": month_count,
                "longest_member_streak": longest_streak,
            },
        }
    ), 200


@admin_attendance_blueprint.get("")
@admin_required
def get_attendance():
    month = request.args.get("month")
    year = request.args.get("year")
    member_id = request.args.get("member_id")
    try:
        month_value = int(month) if month is not None else None
        year_value = int(year) if year is not None else None
        member_value = int(member_id) if member_id is not None else None
    except ValueError:
        return _error("month, year, and member_id must be integers.", 400)
    if month_value is not None and not 1 <= month_value <= 12:
        return _error("month must be between 1 and 12.", 400)
    if year_value is not None and not 1 <= year_value <= 9999:
        return _error("year must be a valid year.", 400)
    if (month_value is None) != (year_value is None):
        return _error("month and year must be provided together.", 400)
    if member_value is not None and member_value < 1:
        return _error("member_id must be positive.", 400)
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "100"))
    except ValueError:
        return _error("page and per_page must be integers.", 400)
    if page < 1 or not 1 <= per_page <= 500:
        return _error("page must be positive and per_page must be between 1 and 500.", 400)

    try:
        query = db.select(Attendance)
        if member_value is not None:
            query = query.where(Attendance.user_id == member_value)
        if month_value is not None:
            month_start = date(year_value, month_value, 1)
            if month_value == 12:
                month_end = date(year_value + 1, 1, 1) if year_value < 9999 else None
            else:
                month_end = date(year_value, month_value + 1, 1)
            query = query.where(Attendance.attendance_date >= month_start)
            if month_end is not None:
                query = query.where(Attendance.attendance_date < month_end)
        total = db.session.scalar(
            db.select(func.count()).select_from(query.subquery())
        ) or 0
        records = db.session.scalars(
            query.order_by(Attendance.attendance_date.desc(), Attendance.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving attendance records.")
        return _error("Unable to retrieve attendance right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Attendance records retrieved successfully.",
            "attendance": [serialize_attendance(item) for item in records],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            },
        }
    ), 200
