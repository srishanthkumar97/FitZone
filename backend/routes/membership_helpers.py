import calendar
from datetime import date, timedelta
from decimal import Decimal

from extensions import db
from membership_plans import MEMBERSHIP_DURATIONS, MEMBERSHIP_PLANS
from models import Membership, MembershipPlan


def add_months(start_date: date, months: int) -> date:
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_end(start_date: date, months: int) -> date:
    return add_months(start_date, months) - timedelta(days=1)


def validate_plan(plan_type: object) -> str | None:
    if not isinstance(plan_type, str):
        return None
    normalized = plan_type.strip().lower()
    return normalized if normalized and len(normalized) <= 40 else None


def validate_duration(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value in MEMBERSHIP_DURATIONS else None


def membership_price(plan_type: str, duration_months: int) -> Decimal:
    plan = db.session.scalar(
        db.select(MembershipPlan).where(MembershipPlan.plan_type == plan_type)
    )
    if plan is not None and not plan.is_active:
        raise ValueError("The selected membership plan is inactive.")
    monthly_price = (
        Decimal(plan.monthly_price)
        if plan is not None
        else Decimal(MEMBERSHIP_PLANS[plan_type]["monthly_price"])
    )
    return (monthly_price * duration_months).quantize(Decimal("0.01"))


def effective_status(membership: Membership, today: date | None = None) -> str:
    today = today or date.today()
    if membership.status == "cancelled":
        return "cancelled"
    if membership.status == "expired" or membership.end_date < today:
        return "expired"
    if membership.start_date > today:
        return "scheduled"
    return "active"


def serialize_membership(membership: Membership, today: date | None = None) -> dict:
    today = today or date.today()
    status = effective_status(membership, today)
    remaining_days = max((membership.end_date - today).days, 0) if status == "active" else 0
    return {
        "id": membership.id,
        "user_id": membership.user_id,
        "plan_name": membership.plan_name,
        "plan_type": membership.plan_type,
        "price": float(membership.price),
        "start_date": membership.start_date.isoformat(),
        "end_date": membership.end_date.isoformat(),
        "remaining_days": remaining_days,
        "status": status,
        "created_at": membership.created_at.isoformat() if membership.created_at else None,
    }
