import logging
import re
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models import MembershipPlan
from .admin_auth import admin_required


admin_plan_blueprint = Blueprint(
    "admin_plans",
    __name__,
    url_prefix="/api/admin/membership-plans",
)
logger = logging.getLogger(__name__)
PLAN_FIELDS = {"plan_type", "name", "monthly_price", "durations_months"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _payload():
    if not request.is_json:
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _serialize(plan):
    return {
        "id": plan.id,
        "plan_type": plan.plan_type,
        "name": plan.name,
        "monthly_price": float(plan.monthly_price),
        "durations_months": plan.durations_months,
        "is_active": plan.is_active,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


def _validate_fields(payload, creating=False):
    if payload.keys() - PLAN_FIELDS:
        return None, "Unsupported membership plan fields."
    values = {}
    if creating or "plan_type" in payload:
        plan_type = payload.get("plan_type")
        if (
            not isinstance(plan_type, str)
            or not re.fullmatch(r"[a-z][a-z0-9_-]{1,39}", plan_type.strip().lower())
        ):
            return None, "plan_type must be a 2-40 character lowercase identifier."
        values["plan_type"] = plan_type.strip().lower()
    if creating or "name" in payload:
        name = payload.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            return None, "name must be between 1 and 80 characters."
        values["name"] = name.strip()
    if creating or "monthly_price" in payload:
        raw_price = payload.get("monthly_price")
        if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float, str)):
            return None, "monthly_price must be a non-negative number."
        try:
            price = Decimal(str(raw_price))
        except (InvalidOperation, ValueError):
            return None, "monthly_price must be a non-negative number."
        if not price.is_finite() or price < 0 or price >= Decimal("100000000"):
            return None, "monthly_price must be a non-negative supported amount."
        values["monthly_price"] = price.quantize(Decimal("0.01"))
    if creating or "durations_months" in payload:
        durations = payload.get("durations_months")
        if (
            not isinstance(durations, list)
            or not durations
            or any(
                isinstance(item, bool)
                or not isinstance(item, int)
                or not 1 <= item <= 36
                for item in durations
            )
            or len(set(durations)) != len(durations)
        ):
            return None, "durations_months must be a non-empty list of unique integers from 1 to 36."
        values["durations_months"] = sorted(durations)
    return values, None


@admin_plan_blueprint.get("")
@admin_required
def list_plans():
    try:
        plans = db.session.scalars(
            db.select(MembershipPlan).order_by(MembershipPlan.id)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while listing membership plans.")
        return _error("Unable to retrieve membership plans right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Membership plans retrieved successfully.",
            "plans": [_serialize(plan) for plan in plans],
        }
    ), 200


@admin_plan_blueprint.post("")
@admin_required
def create_plan():
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    values, error = _validate_fields(payload, creating=True)
    if error:
        return _error(error, 400)
    plan = MembershipPlan(**values)
    db.session.add(plan)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("A plan with this plan_type already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while creating a membership plan.")
        return _error("Unable to create the membership plan right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Membership plan created successfully.",
            "plan": _serialize(plan),
        }
    ), 201


@admin_plan_blueprint.put("/<int:plan_id>")
@admin_required
def update_plan(plan_id: int):
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload:
        return _error("Provide at least one plan field to update.", 400)
    values, error = _validate_fields(payload)
    if error:
        return _error(error, 400)
    plan = db.session.get(MembershipPlan, plan_id)
    if plan is None:
        return _error("Membership plan not found.", 404)
    for key, value in values.items():
        setattr(plan, key, value)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("A plan with this plan_type already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating a membership plan.")
        return _error("Unable to update the membership plan right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Membership plan updated successfully.",
            "plan": _serialize(plan),
        }
    ), 200


@admin_plan_blueprint.delete("/<int:plan_id>")
@admin_required
def deactivate_plan(plan_id: int):
    plan = db.session.get(MembershipPlan, plan_id)
    if plan is None:
        return _error("Membership plan not found.", 404)
    if not plan.is_active:
        return _error("Membership plan is already inactive.", 409)
    plan.is_active = False
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while deactivating a membership plan.")
        return _error("Unable to deactivate the membership plan right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Membership plan deactivated successfully.",
            "plan": _serialize(plan),
        }
    ), 200
