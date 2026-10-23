from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, UniqueConstraint, func

from extensions import db


class Attendance(db.Model):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "attendance_date",
            name="uq_attendance_user_date",
        ),
        CheckConstraint(
            "status IN ('checked_in', 'checked_out')",
            name="ck_attendance_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attendance_date = db.Column(Date, nullable=False, index=True)
    check_in_time = db.Column(DateTime, nullable=False)
    check_out_time = db.Column(DateTime, nullable=True)
    status = db.Column(
        db.String(16),
        nullable=False,
        default="checked_in",
        server_default="checked_in",
    )
    created_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="attendance_records")
