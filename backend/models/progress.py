from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, Text, func

from extensions import db


class Progress(db.Model):
    __tablename__ = "progress"
    __table_args__ = (
        CheckConstraint("weight IS NULL OR weight > 0", name="ck_progress_weight_positive"),
        CheckConstraint("height IS NULL OR height > 0", name="ck_progress_height_positive"),
        CheckConstraint(
            "body_fat IS NULL OR (body_fat >= 0 AND body_fat <= 100)",
            name="ck_progress_body_fat_range",
        ),
        CheckConstraint("chest IS NULL OR chest > 0", name="ck_progress_chest_positive"),
        CheckConstraint("waist IS NULL OR waist > 0", name="ck_progress_waist_positive"),
        CheckConstraint("arms IS NULL OR arms > 0", name="ck_progress_arms_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    record_date = db.Column(Date, nullable=False, index=True)
    weight = db.Column(Numeric(6, 2), nullable=True)
    height = db.Column(Numeric(6, 2), nullable=True)
    body_fat = db.Column(Numeric(5, 2), nullable=True)
    chest = db.Column(Numeric(6, 2), nullable=True)
    waist = db.Column(Numeric(6, 2), nullable=True)
    arms = db.Column(Numeric(6, 2), nullable=True)
    notes = db.Column(Text, nullable=True)
    created_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="progress_records")
