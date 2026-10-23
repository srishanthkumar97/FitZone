from flask import Blueprint

from .auth import auth_blueprint
from .admin_memberships import admin_membership_blueprint
from .admin_attendance import admin_attendance_blueprint
from .admin_announcements import admin_announcement_blueprint
from .admin_dashboard import admin_dashboard_blueprint
from .admin_members import admin_member_blueprint
from .admin_plans import admin_plan_blueprint
from .attendance import attendance_blueprint
from .dashboard import dashboard_blueprint
from .health import health_blueprint
from .memberships import membership_blueprint
from .progress import progress_blueprint
from .workouts import workout_blueprint


api_blueprint = Blueprint("api", __name__, url_prefix="/api")
api_blueprint.register_blueprint(health_blueprint)

__all__ = [
    "admin_announcement_blueprint",
    "admin_dashboard_blueprint",
    "admin_member_blueprint",
    "admin_membership_blueprint",
    "admin_plan_blueprint",
    "admin_attendance_blueprint",
    "api_blueprint",
    "attendance_blueprint",
    "auth_blueprint",
    "dashboard_blueprint",
    "membership_blueprint",
    "progress_blueprint",
    "workout_blueprint",
]
