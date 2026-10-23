import logging
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import generate_password_hash

from extensions import db
from models import Attendance, Membership, Payment, User
from utils.auth_validation import validate_email, validate_phone
from .admin_auth import admin_required
from .attendance_helpers import serialize_attendance
from .membership_helpers import effective_status, serialize_membership


admin_member_blueprint = Blueprint(
    "admin_members",
    __name__,
    url_prefix="/api/admin/members",
)
logger = logging.getLogger(__name__)
CREATE_FIELDS = {"name", "email", "phone", "password"}
EDIT_FIELDS = {"name", "email", "phone", "fitness_goal", "date_of_birth", "gender", "is_active"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _json_object():
    if not request.is_json:
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _serialize_member(user: User, membership: Membership | None):
    today = date.today()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "status": "active" if user.is_active else "inactive",
        "fitness_goal": user.fitness_goal,
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "gender": user.gender,
        "profile_photo": user.profile_photo,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "membership_status": effective_status(membership, today) if membership else "none",
        "membership": serialize_membership(membership, today) if membership else None,
    }


def _latest_memberships(user_ids):
    if not user_ids:
        return {}
    memberships = db.session.scalars(
        db.select(Membership)
        .where(Membership.user_id.in_(user_ids))
        .order_by(Membership.user_id, Membership.created_at.desc(), Membership.id.desc())
    ).all()
    latest = {}
    for membership in memberships:
        latest.setdefault(membership.user_id, membership)
    return latest


def _validate_member_edits(payload, creating=False):
    fields = CREATE_FIELDS if creating else EDIT_FIELDS
    if payload.keys() - fields:
        return None, "Unsupported member fields."
    values = {}
    if creating or "name" in payload:
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            return None, "name must be between 1 and 120 characters."
        values["name"] = name.strip()
    if creating or "email" in payload:
        email = validate_email(payload.get("email"))
        if email is None:
            return None, "Enter a valid email address."
        values["email"] = email
    if creating or "phone" in payload:
        phone = validate_phone(payload.get("phone"))
        if phone is None:
            return None, "Enter a valid phone number."
        values["phone"] = phone
    if creating:
        password = payload.get("password")
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            return None, "Password must be between 8 and 128 characters."
        values["password_hash"] = generate_password_hash(password)
    if "fitness_goal" in payload:
        goal = payload["fitness_goal"]
        if goal is not None and (
            not isinstance(goal, str) or not goal.strip() or len(goal.strip()) > 80
        ):
            return None, "fitness_goal must be at most 80 characters or null."
        values["fitness_goal"] = goal.strip() if isinstance(goal, str) else None
    if "gender" in payload:
        gender = payload["gender"]
        if gender is not None and (
            not isinstance(gender, str)
            or gender.strip().lower()
            not in {"male", "female", "non-binary", "other", "prefer_not_to_say"}
        ):
            return None, "gender is not an accepted value."
        values["gender"] = gender.strip().lower() if isinstance(gender, str) else None
    if "date_of_birth" in payload:
        raw_date = payload["date_of_birth"]
        if raw_date is None:
            values["date_of_birth"] = None
        elif isinstance(raw_date, str):
            try:
                parsed = date.fromisoformat(raw_date)
            except ValueError:
                return None, "date_of_birth must use YYYY-MM-DD format."
            if parsed >= date.today():
                return None, "date_of_birth must be a past date."
            values["date_of_birth"] = parsed
        else:
            return None, "date_of_birth must use YYYY-MM-DD format."
    if "is_active" in payload:
        if not isinstance(payload["is_active"], bool):
            return None, "is_active must be true or false."
        values["is_active"] = payload["is_active"]
    return values, None


@admin_member_blueprint.get("")
@admin_required
def list_members():
    search = request.args.get("search", "").strip()
    status = request.args.get("status")
    membership_filter = request.args.get("membership")
    if status not in (None, "active", "inactive"):
        return _error("status must be active or inactive.", 400)
    if membership_filter not in (None, "active", "scheduled", "expired", "cancelled", "none"):
        return _error("membership must be active, scheduled, expired, cancelled, or none.", 400)
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "25"))
    except ValueError:
        return _error("page and per_page must be integers.", 400)
    if page < 1 or not 1 <= per_page <= 100:
        return _error("page must be positive and per_page must be between 1 and 100.", 400)

    try:
        query = db.select(User).where(User.role == "member")
        if status is not None:
            query = query.where(User.is_active.is_(status == "active"))
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(User.name.ilike(pattern), User.email.ilike(pattern), User.phone.ilike(pattern))
            )
        all_users = db.session.scalars(query.order_by(User.created_at.desc(), User.id.desc())).all()
        memberships = _latest_memberships([item.id for item in all_users])
        rows = [
            member
            for member in all_users
            if membership_filter is None
            or (
                effective_status(memberships.get(member.id), date.today())
                if memberships.get(member.id)
                else "none"
            )
            == membership_filter
        ]
        total = len(rows)
        selected = rows[(page - 1) * per_page : page * per_page]
        serialized = [
            _serialize_member(member, memberships.get(member.id))
            for member in selected
        ]
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while listing members.")
        return _error("Unable to retrieve members right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Members retrieved successfully.",
            "members": serialized,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
            },
        }
    ), 200


@admin_member_blueprint.post("")
@admin_required
def create_member():
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    values, error = _validate_member_edits(payload, creating=True)
    if error:
        return _error(error, 400)
    user = User(**values, role="member", is_active=True)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("An account with this email already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while creating a member.")
        return _error("Unable to create the member right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Member created successfully.",
            "member": _serialize_member(user, None),
        }
    ), 201


@admin_member_blueprint.get("/<int:member_id>")
@admin_required
def get_member(member_id: int):
    try:
        member = db.session.scalar(
            db.select(User).where(User.id == member_id, User.role == "member")
        )
        if member is None:
            return _error("Member not found.", 404)
        memberships = db.session.scalars(
            db.select(Membership)
            .where(Membership.user_id == member.id)
            .order_by(Membership.created_at.desc(), Membership.id.desc())
        ).all()
        attendance = db.session.scalars(
            db.select(Attendance)
            .where(Attendance.user_id == member.id)
            .order_by(Attendance.attendance_date.desc(), Attendance.id.desc())
            .limit(100)
        ).all()
        payments = db.session.scalars(
            db.select(Payment)
            .where(Payment.user_id == member.id)
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(100)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving member detail.")
        return _error("Unable to retrieve member information right now.", 503)
    latest = memberships[0] if memberships else None
    return jsonify(
        {
            "success": True,
            "message": "Member details retrieved successfully.",
            "member": _serialize_member(member, latest),
            "memberships": [serialize_membership(item) for item in memberships],
            "attendance": [serialize_attendance(item) for item in attendance],
            "payments": [
                {
                    "id": payment.id,
                    "membership_id": payment.membership_id,
                    "amount": float(payment.amount),
                    "status": payment.status,
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                }
                for payment in payments
            ],
        }
    ), 200


@admin_member_blueprint.put("/<int:member_id>")
@admin_required
def update_member(member_id: int):
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload:
        return _error("Provide at least one member field to update.", 400)
    values, error = _validate_member_edits(payload)
    if error:
        return _error(error, 400)
    member = db.session.scalar(
        db.select(User).where(User.id == member_id, User.role == "member")
    )
    if member is None:
        return _error("Member not found.", 404)
    for field, value in values.items():
        setattr(member, field, value)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("An account with this email already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating a member.")
        return _error("Unable to update the member right now.", 503)
    latest = _latest_memberships([member.id]).get(member.id)
    return jsonify(
        {
            "success": True,
            "message": "Member updated successfully.",
            "member": _serialize_member(member, latest),
        }
    ), 200


@admin_member_blueprint.delete("/<int:member_id>")
@admin_required
def deactivate_member(member_id: int):
    member = db.session.scalar(
        db.select(User).where(User.id == member_id, User.role == "member")
    )
    if member is None:
        return _error("Member not found.", 404)
    if not member.is_active:
        return _error("Member is already deactivated.", 409)
    member.is_active = False
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while deactivating a member.")
        return _error("Unable to deactivate the member right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Member deactivated successfully.",
            "member_id": member.id,
            "is_active": False,
        }
    ), 200
