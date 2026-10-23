from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, func

from extensions import db


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (
        CheckConstraint("duration > 0", name="ck_workouts_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_date = db.Column(Date, nullable=False, index=True)
    workout_type = db.Column(String(80), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    notes = db.Column(Text, nullable=True)
    created_at = db.Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="workouts")
    exercises = db.relationship(
        "Exercise",
        back_populates="workout",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Exercise.id",
    )


class Exercise(db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("sets IS NULL OR sets > 0", name="ck_exercises_sets_positive"),
        CheckConstraint("reps IS NULL OR reps > 0", name="ck_exercises_reps_positive"),
        CheckConstraint(
            "weight IS NULL OR weight >= 0",
            name="ck_exercises_weight_nonnegative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_name = db.Column(String(120), nullable=False)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Numeric(8, 2), nullable=True)

    workout = db.relationship("Workout", back_populates="exercises")
