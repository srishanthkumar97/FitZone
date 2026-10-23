from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func

from extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(String(160), nullable=False)
    body = db.Column(Text, nullable=False)
    is_active = db.Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        index=True,
    )
    created_by = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
