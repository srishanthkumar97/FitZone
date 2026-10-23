import logging
from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from membership_plans import MEMBERSHIP_DURATIONS, MEMBERSHIP_PLANS
from models import Membership, MembershipPlan, User
from .membership_helpers import serialize_membership


membership_blueprint = Blueprint("membership", __name__, url_prefix="/api/membership")
logger = logging.getLogger(__name__)


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _current_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id)


def _expire_past_memberships(user_id: int, today: date) -> None:
    db.session.execute(
        update(Membership)
        .where(
            Membership.user_id == user_id,
            Membership.status == "active",
            Membership.end_date < today,
        )
        .values(status="expired")
    )


@membership_blueprint.get("/plans")
def get_plans():
    try:
        configured_plans = db.session.scalars(
            db.select(MembershipPlan)
            .where(MembershipPlan.is_active.is_(True))
            .order_by(MembershipPlan.id)
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving membership plans.")
        return _error("Unable to retrieve membership plans right now.", 503)

    if configured_plans:
        configured_by_type = {plan.plan_type: plan for plan in configured_plans}
        plan_entries = []
        for plan_type, fallback in MEMBERSHIP_PLANS.items():
            configured = configured_by_type.pop(plan_type, None)
            if configured is None:
                plan_entries.append(
                    (plan_type, fallback["name"], fallback["monthly_price"], list(MEMBERSHIP_DURATIONS))
                )
            elif configured.is_active:
                plan_entries.append(
                    (
                        configured.plan_type,
                        configured.name,
                        configured.monthly_price,
                        configured.durations_months,
                    )
                )
        plan_entries.extend(
            (plan.plan_type, plan.name, plan.monthly_price, plan.durations_months)
            for plan in configured_by_type.values()
            if plan.is_active
        )
        plans = [
            {
                "plan_type": plan_type,
                "plan_name": name,
                "monthly_price": float(monthly_price),
                "durations_months": durations,
                "prices": {
                    str(months): float(monthly_price * months)
                    for months in durations
                },
            }
            for plan_type, name, monthly_price, durations in plan_entries
        ]
    else:
        plans = [
            {
                "plan_type": plan_type,
                "plan_name": plan["name"],
                "monthly_price": plan["monthly_price"],
                "durations_months": list(MEMBERSHIP_DURATIONS),
                "prices": {
                    str(months): plan["monthly_price"] * months
                    for months in MEMBERSHIP_DURATIONS
                },
            }
            for plan_type, plan in MEMBERSHIP_PLANS.items()
        ]
    return jsonify(
        {
            "success": True,
            "message": "Membership plans retrieved successfully",
            "plans": plans,
        }
    ), 200


@membership_blueprint.get("/current")
@jwt_required()
def get_current_membership():
    user = _current_user()
    if user is None:
        return _error("The account for this token no longer exists.", 401)
    if user.role != "member" or not user.is_active:
        return _error("An active member account is required.", 403)

    today = date.today()
    try:
        _expire_past_memberships(user.id, today)
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
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving the current membership.")
        return _error("Unable to retrieve the current membership right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Current membership retrieved successfully",
            "membership": serialize_membership(membership, today) if membership else None,
        }
    ), 200


@membership_blueprint.get("/history")
@jwt_required()
def get_membership_history():
    user = _current_user()
    if user is None:
        return _error("The account for this token no longer exists.", 401)
    if user.role != "member" or not user.is_active:
        return _error("An active member account is required.", 403)

    today = date.today()
    try:
        _expire_past_memberships(user.id, today)
        memberships = db.session.scalars(
            db.select(Membership)
            .where(Membership.user_id == user.id)
            .order_by(Membership.created_at.desc(), Membership.id.desc())
        ).all()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving membership history.")
        return _error("Unable to retrieve membership history right now.", 503)

    return jsonify(
        {
            "success": True,
            "message": "Membership history retrieved successfully",
            "memberships": [
                serialize_membership(membership, today) for membership in memberships
            ],
        }
    ), 200
