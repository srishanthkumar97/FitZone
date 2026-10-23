import logging
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from membership_plans import MEMBERSHIP_PLANS
from models import Membership, MembershipPlan, User
from .admin_auth import admin_required
from .membership_helpers import (
    period_end,
    serialize_membership,
    validate_plan,
)


admin_membership_blueprint = Blueprint(
    "admin_memberships",
    __name__,
    url_prefix="/api/admin/memberships",
)
logger = logging.getLogger(__name__)
CREATE_FIELDS = {"user_id", "plan_type", "duration_months"}
UPDATE_FIELDS = {"plan_type", "duration_months"}
RENEW_FIELDS = {"plan_type", "duration_months"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _json_object():
    if not request.is_json:
        return None
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


def _validated_plan_and_duration(payload: dict):
    if "plan_type" not in payload:
        return None, None, "plan_type is required."
    if "duration_months" not in payload:
        return None, None, "duration_months is required."

    plan_type = validate_plan(payload.get("plan_type"))
    if plan_type is None:
        return None, None, "plan_type must be a valid plan identifier."
    plan = db.session.scalar(
        db.select(MembershipPlan).where(MembershipPlan.plan_type == plan_type)
    )
    if plan is not None and not plan.is_active:
        return None, None, "This membership plan is inactive."
    if plan is None and plan_type not in MEMBERSHIP_PLANS:
        return None, None, "An active membership plan with this plan_type was not found."
    durations = plan.durations_months if plan else [1, 3, 6]
    duration = payload.get("duration_months")
    if isinstance(duration, bool) or not isinstance(duration, int) or duration not in durations:
        return None, None, f"duration_months must be one of: {', '.join(map(str, durations))}."
    return plan_type, duration, None


def _active_plan(plan_type: str):
    plan = db.session.scalar(
        db.select(MembershipPlan).where(MembershipPlan.plan_type == plan_type)
    )
    if plan is not None:
        return (plan.name, Decimal(plan.monthly_price)) if plan.is_active else (None, None)
    fallback = MEMBERSHIP_PLANS.get(plan_type)
    if fallback is None:
        return None, None
    return fallback["name"], Decimal(fallback["monthly_price"])


def _overlapping_active_membership(user_id: int, start_date: date, end_date: date, omit_id=None):
    query = db.select(Membership.id).where(
        Membership.user_id == user_id,
        Membership.status == "active",
        Membership.start_date <= end_date,
        Membership.end_date >= start_date,
    )
    if omit_id is not None:
        query = query.where(Membership.id != omit_id)
    return db.session.scalar(query.with_for_update())


def _expire_past_memberships(user_id: int, today: date) -> None:
    past_memberships = db.session.scalars(
        db.select(Membership)
        .where(
            Membership.user_id == user_id,
            Membership.status == "active",
            Membership.end_date < today,
        )
        .with_for_update()
    ).all()
    for membership in past_memberships:
        membership.status = "expired"


def _lock_membership_and_owner(membership_id: int):
    membership = db.session.get(Membership, membership_id)
    if membership is None:
        return None
    db.session.execute(
        db.select(User.id).where(User.id == membership.user_id).with_for_update()
    )
    return db.session.scalar(
        db.select(Membership)
        .where(Membership.id == membership_id)
        .with_for_update()
    )


@admin_membership_blueprint.get("")
@admin_required
def list_memberships():
    try:
        memberships = db.session.scalars(
            db.select(Membership).order_by(Membership.created_at.desc(), Membership.id.desc())
        ).all()
        return jsonify(
            {
                "success": True,
                "message": "Memberships retrieved successfully",
                "memberships": [serialize_membership(item) for item in memberships],
            }
        ), 200
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while listing memberships.")
        return _error("Unable to retrieve memberships right now.", 503)


@admin_membership_blueprint.post("")
@admin_required
def assign_membership():
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if payload.keys() - CREATE_FIELDS:
        return _error("Only user_id, plan_type, and duration_months are accepted.", 400)
    missing = CREATE_FIELDS - payload.keys()
    if missing:
        return _error(f"Missing required field(s): {', '.join(sorted(missing))}.", 400)

    user_id = payload["user_id"]
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id < 1:
        return _error("user_id must be a positive integer.", 400)
    plan_type, duration, error = _validated_plan_and_duration(payload)
    if error:
        return _error(error, 400)

    try:
        member = db.session.scalar(
            db.select(User).where(User.id == user_id).with_for_update()
        )
        if member is None:
            return _error("Member not found.", 404)
        if member.role != "member":
            return _error("Memberships can only be assigned to member accounts.", 400)
        if not member.is_active:
            return _error("Memberships cannot be assigned to deactivated members.", 400)

        today = date.today()
        _expire_past_memberships(user_id, today)
        end_date = period_end(today, duration)
        if _overlapping_active_membership(user_id, today, end_date) is not None:
            db.session.rollback()
            return _error("This member already has an active membership. Renew it instead.", 409)

        plan_name, monthly_price = _active_plan(plan_type)
        if plan_name is None:
            return _error("An active membership plan was not found.", 400)
        membership = Membership(
            user_id=user_id,
            plan_name=plan_name,
            plan_type=plan_type,
            price=(monthly_price * duration).quantize(Decimal("0.01")),
            start_date=today,
            end_date=end_date,
            status="active",
        )
        db.session.add(membership)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while assigning a membership.")
        return _error("Unable to assign the membership right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Membership assigned successfully",
            "membership": serialize_membership(membership),
        }
    ), 201


@admin_membership_blueprint.put("/<int:membership_id>")
@admin_required
def update_membership(membership_id: int):
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload or payload.keys() - UPDATE_FIELDS:
        return _error(
            "Provide plan_type and/or duration_months to update the membership.",
            400,
        )

    try:
        membership = _lock_membership_and_owner(membership_id)
        if membership is None:
            return _error("Membership not found.", 404)
        if membership.status == "cancelled":
            return _error("A cancelled membership cannot be updated.", 409)

        plan_type = validate_plan(payload.get("plan_type", membership.plan_type))
        if plan_type is None:
            return _error("plan_type must be a valid plan identifier.", 400)
        plan_name, monthly_price = _active_plan(plan_type)
        if plan_name is None:
            return _error("An active membership plan with this plan_type was not found.", 400)
        plan_record = db.session.scalar(
            db.select(MembershipPlan).where(
                MembershipPlan.plan_type == plan_type,
                MembershipPlan.is_active.is_(True),
            )
        )
        durations = plan_record.durations_months if plan_record else [1, 3, 6]
        duration = payload.get("duration_months")
        if duration is not None:
            if isinstance(duration, bool) or not isinstance(duration, int) or duration not in durations:
                return _error(
                    f"duration_months must be one of: {', '.join(map(str, durations))}.",
                    400,
                )
        else:
            current_days = (membership.end_date - membership.start_date).days + 1
            duration = next(
                (
                    months
                    for months in durations
                    if (period_end(membership.start_date, months) - membership.start_date).days + 1
                    == current_days
                ),
                None,
            )
            if duration is None:
                return _error(
                    "Cannot infer plan duration; provide duration_months.",
                    400,
                )

        new_end_date = period_end(membership.start_date, duration)
        conflict_id = _overlapping_active_membership(
            membership.user_id,
            membership.start_date,
            new_end_date,
            omit_id=membership.id,
        )
        if conflict_id is not None:
            db.session.rollback()
            return _error("This update overlaps another active membership.", 409)

        membership.plan_type = plan_type
        membership.plan_name = plan_name
        membership.price = (monthly_price * duration).quantize(Decimal("0.01"))
        membership.end_date = new_end_date
        membership.status = "expired" if new_end_date < date.today() else "active"
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating a membership.")
        return _error("Unable to update the membership right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Membership updated successfully",
            "membership": serialize_membership(membership),
        }
    ), 200


@admin_membership_blueprint.post("/<int:membership_id>/renew")
@admin_required
def renew_membership(membership_id: int):
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if payload.keys() - RENEW_FIELDS:
        return _error("Only plan_type and duration_months are accepted.", 400)

    try:
        membership = _lock_membership_and_owner(membership_id)
        if membership is None:
            return _error("Membership not found.", 404)
        if membership.status == "cancelled":
            return _error("A cancelled membership cannot be renewed.", 409)

        plan_type = validate_plan(payload.get("plan_type", membership.plan_type))
        if plan_type is None:
            return _error("plan_type must be a valid plan identifier.", 400)
        plan_name, monthly_price = _active_plan(plan_type)
        if plan_name is None:
            return _error("An active membership plan with this plan_type was not found.", 400)
        plan_record = db.session.scalar(
            db.select(MembershipPlan).where(
                MembershipPlan.plan_type == plan_type,
                MembershipPlan.is_active.is_(True),
            )
        )
        durations = plan_record.durations_months if plan_record else [1, 3, 6]
        duration_value = payload.get("duration_months", 1)
        if (
            isinstance(duration_value, bool)
            or not isinstance(duration_value, int)
            or duration_value not in durations
        ):
            return _error(
                f"duration_months must be one of: {', '.join(map(str, durations))}.",
                400,
            )
        duration = duration_value

        today = date.today()
        _expire_past_memberships(membership.user_id, today)
        if membership.end_date >= today:
            renewal_start = membership.start_date
            renewal_end = period_end(membership.end_date + timedelta(days=1), duration)
        else:
            renewal_start = today
            renewal_end = period_end(renewal_start, duration)

        membership.plan_type = plan_type
        membership.plan_name = plan_name
        membership.price = (
            membership.price + (monthly_price * duration).quantize(Decimal("0.01"))
            if membership.end_date >= today
            else (monthly_price * duration).quantize(Decimal("0.01"))
        )
        membership.start_date = renewal_start
        membership.end_date = renewal_end
        membership.status = "active"
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while renewing a membership.")
        return _error("Unable to renew the membership right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Membership renewed successfully",
            "membership": serialize_membership(membership),
        }
    ), 200


@admin_membership_blueprint.delete("/<int:membership_id>")
@admin_required
def cancel_membership(membership_id: int):
    try:
        membership = _lock_membership_and_owner(membership_id)
        if membership is None:
            return _error("Membership not found.", 404)
        if membership.status == "cancelled":
            return _error("Membership is already cancelled.", 409)
        membership.status = "cancelled"
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while cancelling a membership.")
        return _error("Unable to cancel the membership right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Membership cancelled successfully",
            "membership": serialize_membership(membership),
        }
    ), 200
