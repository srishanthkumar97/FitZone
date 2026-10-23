import logging
from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Attendance, Membership, Notification, Progress, User, Workout
from .attendance_helpers import attendance_streaks
from .membership_helpers import serialize_membership
from .progress import _serialize_progress
from .workouts import serialize_workout


dashboard_blueprint = Blueprint("dashboard", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@dashboard_blueprint.get("/dashboard")
@jwt_required()
def get_dashboard():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid account token."}), 401

    try:
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify(
                {"success": False, "message": "The account for this token no longer exists."}
            ), 401
        if user.role != "member":
            return jsonify({"success": False, "message": "Member access is required."}), 403
        if not user.is_active:
            return jsonify({"success": False, "message": "This member account is deactivated."}), 403

        today = date.today()
        month_start = today.replace(day=1)
        membership = db.session.scalar(
            db.select(Membership)
            .where(
                Membership.user_id == user.id,
                Membership.status == "active",
                Membership.start_date <= today,
                Membership.end_date >= today,
            )
            .order_by(Membership.end_date.desc(), Membership.id.desc())
        )
        attendance_dates = db.session.scalars(
            db.select(Attendance.attendance_date)
            .where(Attendance.user_id == user.id)
            .order_by(Attendance.attendance_date)
        ).all()
        current_streak, longest_streak = attendance_streaks(attendance_dates, today)
        last_attendance = max(
            (day for day in attendance_dates if day <= today),
            default=None,
        )
        current_month_attendance = sum(
            month_start <= day <= today for day in attendance_dates
        )
        latest_progress = db.session.scalar(
            db.select(Progress)
            .where(Progress.user_id == user.id)
            .order_by(Progress.record_date.desc(), Progress.id.desc())
        )
        recent_workouts = db.session.scalars(
            db.select(Workout)
            .where(Workout.user_id == user.id)
            .order_by(Workout.workout_date.desc(), Workout.id.desc())
            .limit(5)
        ).all()
        recent_notifications = db.session.scalars(
            db.select(Notification)
            .where(Notification.is_active.is_(True))
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(5)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving member dashboard.")
        return jsonify(
            {"success": False, "message": "Unable to retrieve the dashboard right now."}
        ), 503

    return jsonify(
        {
            "success": True,
            "message": "Dashboard retrieved successfully.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "fitness_goal": user.fitness_goal,
                "profile_photo": user.profile_photo,
            },
            "membership": serialize_membership(membership, today) if membership else None,
            "attendance": {
                "total_attendance_days": len(attendance_dates),
                "current_month_attendance": current_month_attendance,
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "last_attendance_date": (
                    last_attendance.isoformat() if last_attendance else None
                ),
            },
            "progress": _serialize_progress(latest_progress) if latest_progress else None,
            "recent_workouts": [serialize_workout(item) for item in recent_workouts],
            "recent_notifications": [
                {
                    "id": item.id,
                    "title": item.title,
                    "body": item.body,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in recent_notifications
            ],
        }
    ), 200
