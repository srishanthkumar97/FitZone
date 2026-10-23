from sqlalchemy import CheckConstraint, Enum, String, func

from extensions import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('member', 'admin')",
            name="ck_users_role",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(String(120), nullable=False)
    email = db.Column(String(255), nullable=False, unique=True, index=True)
    phone = db.Column(String(32), nullable=True, index=True)
    password_hash = db.Column(String(255), nullable=False)
    role = db.Column(
        Enum("member", "admin", name="user_role"),
        nullable=False,
        default="member",
        server_default="member",
        index=True,
    )
    fitness_goal = db.Column(String(80), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(String(32), nullable=True)
    profile_photo = db.Column(String(2048), nullable=True)
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default="1",
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    memberships = db.relationship(
        "Membership",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    attendance_records = db.relationship(
        "Attendance",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    workouts = db.relationship(
        "Workout",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    progress_records = db.relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    payments = db.relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
