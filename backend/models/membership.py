from sqlalchemy import CheckConstraint, Enum, Numeric, String, func

from extensions import db


class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_memberships_price_nonnegative"),
        CheckConstraint("end_date >= start_date", name="ck_memberships_date_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_name = db.Column(String(80), nullable=False)
    plan_type = db.Column(
        String(40),
        nullable=False,
        index=True,
    )
    price = db.Column(Numeric(10, 2), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(
        Enum("active", "expired", "cancelled", name="membership_status"),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="memberships")

    def __repr__(self) -> str:
        return f"<Membership id={self.id} user_id={self.user_id} plan={self.plan_type!r}>"
