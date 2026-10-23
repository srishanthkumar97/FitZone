from sqlalchemy import Boolean, CheckConstraint, Numeric, String, func
from sqlalchemy.types import JSON

from extensions import db


class MembershipPlan(db.Model):
    __tablename__ = "membership_plans"
    __table_args__ = (
        CheckConstraint(
            "monthly_price >= 0",
            name="ck_membership_plans_price_nonnegative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    plan_type = db.Column(String(40), nullable=False, unique=True, index=True)
    name = db.Column(String(80), nullable=False)
    monthly_price = db.Column(Numeric(10, 2), nullable=False)
    durations_months = db.Column(JSON, nullable=False, default=lambda: [1, 3, 6])
    is_active = db.Column(Boolean, nullable=False, default=True, server_default="1", index=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
