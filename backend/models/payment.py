from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func

from extensions import db


class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'refunded')",
            name="ck_payments_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_id = db.Column(
        db.Integer,
        db.ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(
        String(16),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    payment_method = db.Column(String(40), nullable=True)
    paid_at = db.Column(DateTime, nullable=True, index=True)
    created_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="payments")
