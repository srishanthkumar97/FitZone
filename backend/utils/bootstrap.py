from decimal import Decimal

from extensions import db
from membership_plans import MEMBERSHIP_DURATIONS, MEMBERSHIP_PLANS
from models import MembershipPlan


def seed_membership_plans() -> int:
    existing_types = set(
        db.session.scalars(db.select(MembershipPlan.plan_type)).all()
    )
    added = 0
    for plan_type, plan_data in MEMBERSHIP_PLANS.items():
        if plan_type in existing_types:
            continue
        db.session.add(
            MembershipPlan(
                plan_type=plan_type,
                name=plan_data["name"],
                monthly_price=Decimal(plan_data["monthly_price"]),
                durations_months=list(MEMBERSHIP_DURATIONS),
            )
        )
        added += 1
    db.session.commit()
    return added
