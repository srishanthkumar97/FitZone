import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import distinct, func, or_
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Attendance, Membership, Payment, User
from .admin_auth import admin_required


admin_dashboard_blueprint = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/api/admin",
)
logger = logging.getLogger(__name__)


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _parse_date_argument(name):
    value = request.args.get(name)
    if value is None:
        return None, None
    try:
        return date.fromisoformat(value), None
    except ValueError:
        return None, f"{name} must use YYYY-MM-DD format."


def _revenue(start: date | None = None, end: date | None = None) -> Decimal:
    query = db.select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.status == "completed",
    )
    if start is not None:
        query = query.where(Payment.paid_at >= datetime.combine(start, time.min))
    if end is not None:
        if end == date.max:
            query = query.where(Payment.paid_at <= datetime.combine(end, time.max))
        else:
            query = query.where(
                Payment.paid_at < datetime.combine(end + timedelta(days=1), time.min)
            )
    return Decimal(db.session.scalar(query) or 0)


@admin_dashboard_blueprint.get("/dashboard")
@admin_required
def get_admin_dashboard():
    start_date, error = _parse_date_argument("start_date")
    if error:
        return _error(error, 400)
    end_date, error = _parse_date_argument("end_date")
    if error:
        return _error(error, 400)
    if (start_date is None) != (end_date is None):
        return _error("Provide both start_date and end_date for a custom range.", 400)
    if start_date and end_date and start_date > end_date:
        return _error("start_date must be on or before end_date.", 400)

    today = date.today()
    month_start = today.replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    expiring_through = today + timedelta(days=7)
    try:
        total_members = db.session.scalar(
            db.select(func.count(User.id)).where(User.role == "member")
        ) or 0
        active_members = db.session.scalar(
            db.select(func.count(distinct(Membership.user_id))).where(
                Membership.status == "active",
                Membership.start_date <= today,
                Membership.end_date >= today,
                Membership.user_id.in_(
                    db.select(User.id).where(User.role == "member", User.is_active.is_(True))
                ),
            )
        ) or 0
        expired_members = db.session.scalar(
            db.select(func.count(distinct(Membership.user_id))).where(
                Membership.status != "cancelled",
                or_(Membership.status == "expired", Membership.end_date < today),
                Membership.user_id.in_(
                    db.select(User.id).where(User.role == "member", User.is_active.is_(True))
                ),
                ~Membership.user_id.in_(
                    db.select(Membership.user_id).where(
                        Membership.status == "active",
                        Membership.start_date <= today,
                        Membership.end_date >= today,
                    )
                ),
            )
        ) or 0
        today_attendance = db.session.scalar(
            db.select(func.count(Attendance.id)).where(
                Attendance.attendance_date == today
            )
        ) or 0
        monthly_attendance = db.session.scalar(
            db.select(func.count(Attendance.id)).where(
                Attendance.attendance_date >= month_start,
                Attendance.attendance_date <= today,
            )
        ) or 0
        members_expiring_soon = db.session.scalar(
            db.select(func.count(distinct(Membership.user_id))).where(
                Membership.status == "active",
                Membership.end_date >= today,
                Membership.end_date <= expiring_through,
                Membership.user_id.in_(
                    db.select(User.id).where(User.role == "member", User.is_active.is_(True))
                ),
            )
        ) or 0
        new_members = db.session.scalar(
            db.select(func.count(User.id)).where(
                User.role == "member",
                User.created_at >= datetime.combine(month_start, time.min),
                User.created_at < datetime.combine(today + timedelta(days=1), time.min),
            )
        ) or 0

        total_revenue = _revenue()
        monthly_revenue = _revenue(month_start, today)
        last_month_revenue = _revenue(last_month_start, last_month_end)
        custom_revenue = (
            _revenue(start_date, end_date) if start_date and end_date else None
        )

        trend_start = today - timedelta(days=6)
        attendance_rows = db.session.execute(
            db.select(Attendance.attendance_date, func.count(Attendance.id))
            .where(
                Attendance.attendance_date >= trend_start,
                Attendance.attendance_date <= today,
            )
            .group_by(Attendance.attendance_date)
        ).all()
        attendance_by_date = {day: count for day, count in attendance_rows}
        revenue_rows = db.session.execute(
            db.select(func.date(Payment.paid_at), func.sum(Payment.amount))
            .where(
                Payment.status == "completed",
                Payment.paid_at >= datetime.combine(trend_start, time.min),
                Payment.paid_at < datetime.combine(today + timedelta(days=1), time.min),
            )
            .group_by(func.date(Payment.paid_at))
        ).all()
        revenue_by_date = {
            day.isoformat() if hasattr(day, "isoformat") else str(day): Decimal(value or 0)
            for day, value in revenue_rows
        }
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving admin dashboard.")
        return _error("Unable to retrieve dashboard statistics right now.", 503)

    daily_trends = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        daily_trends.append(
            {
                "date": day.isoformat(),
                "attendance": int(attendance_by_date.get(day, 0)),
                "revenue": float(revenue_by_date.get(day.isoformat(), Decimal("0"))),
            }
        )

    response = {
        "success": True,
        "message": "Admin dashboard retrieved successfully.",
        "statistics": {
            "total_members": int(total_members),
            "active_members": int(active_members),
            "expired_members": int(expired_members),
            "today_attendance": int(today_attendance),
            "monthly_attendance": int(monthly_attendance),
            "members_expiring_soon": int(members_expiring_soon),
            "total_revenue": float(total_revenue),
            "monthly_revenue": float(monthly_revenue),
            "last_month_revenue": float(last_month_revenue),
            "new_members": int(new_members),
        },
        "trends": {"daily_last_7_days": daily_trends},
    }
    if custom_revenue is not None:
        response["statistics"]["custom_period_revenue"] = float(custom_revenue)
        response["statistics"]["custom_period"] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    return jsonify(response), 200
