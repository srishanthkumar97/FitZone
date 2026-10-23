import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Exercise, User, Workout


workout_blueprint = Blueprint("workouts", __name__, url_prefix="/api/workouts")
logger = logging.getLogger(__name__)
WORKOUT_FIELDS = {"workout_date", "workout_type", "duration", "notes", "exercises"}
EXERCISE_FIELDS = {"exercise_name", "sets", "reps", "weight"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _member():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None
    user = db.session.get(User, user_id)
    return user if user and user.role == "member" and user.is_active else None


def _payload():
    if not request.is_json:
        return None
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _positive_integer(value, field, allow_none=False):
    if value is None and allow_none:
        return None, None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None, f"{field} must be a positive integer."
    return value, None


def _decimal_value(value, field, *, allow_none=False, allow_zero=False):
    if value is None and allow_none:
        return None, None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None, f"{field} must be a valid number."
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, f"{field} must be a valid number."
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        qualifier = "non-negative" if allow_zero else "greater than zero"
        return None, f"{field} must be {qualifier}."
    if len(number.as_tuple().digits) > 8 or abs(number) >= Decimal("1000000"):
        return None, f"{field} is outside the supported range."
    return number, None


def _normalize_exercises(value):
    if not isinstance(value, list):
        return None, "exercises must be a list."
    normalized = []
    for index, exercise in enumerate(value):
        prefix = f"exercises[{index}]"
        if not isinstance(exercise, dict):
            return None, f"{prefix} must be an object."
        if exercise.keys() - EXERCISE_FIELDS:
            return None, f"{prefix} contains unsupported fields."
        name = exercise.get("exercise_name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            return None, f"{prefix}.exercise_name must be between 1 and 120 characters."
        record = {"exercise_name": name.strip()}
        for key in ("sets", "reps"):
            if key in exercise:
                parsed, error = _positive_integer(exercise[key], f"{prefix}.{key}", True)
                if error:
                    return None, error
                record[key] = parsed
        if "weight" in exercise:
            parsed, error = _decimal_value(
                exercise["weight"],
                f"{prefix}.weight",
                allow_none=True,
                allow_zero=True,
            )
            if error:
                return None, error
            record["weight"] = parsed
        normalized.append(record)
    return normalized, None


def serialize_exercise(exercise: Exercise) -> dict:
    return {
        "id": exercise.id,
        "exercise_name": exercise.exercise_name,
        "sets": exercise.sets,
        "reps": exercise.reps,
        "weight": float(exercise.weight) if exercise.weight is not None else None,
    }


def serialize_workout(workout: Workout) -> dict:
    return {
        "id": workout.id,
        "user_id": workout.user_id,
        "workout_date": workout.workout_date.isoformat(),
        "workout_type": workout.workout_type,
        "duration": workout.duration,
        "notes": workout.notes,
        "created_at": workout.created_at.isoformat() if workout.created_at else None,
        "exercises": [serialize_exercise(item) for item in workout.exercises],
    }


def _apply_fields(workout, payload, creating=False):
    if creating or "workout_date" in payload:
        value = payload.get("workout_date", date.today().isoformat())
        parsed_date = _parse_date(value)
        if parsed_date is None:
            return "workout_date must use YYYY-MM-DD format."
        workout.workout_date = parsed_date

    if creating or "workout_type" in payload:
        workout_type = payload.get("workout_type")
        if (
            not isinstance(workout_type, str)
            or not workout_type.strip()
            or len(workout_type.strip()) > 80
        ):
            return "workout_type must be between 1 and 80 characters."
        workout.workout_type = workout_type.strip()

    if creating or "duration" in payload:
        duration, error = _positive_integer(payload.get("duration"), "duration")
        if error:
            return error
        workout.duration = duration

    if "notes" in payload:
        notes = payload["notes"]
        if notes is not None and (not isinstance(notes, str) or len(notes) > 5000):
            return "notes must be a string of at most 5000 characters or null."
        workout.notes = notes.strip() if isinstance(notes, str) else None

    if "exercises" in payload:
        exercises, error = _normalize_exercises(payload["exercises"])
        if error:
            return error
        workout.exercises = [Exercise(**values) for values in exercises]
    elif creating:
        workout.exercises = []
    return None


@workout_blueprint.post("")
@jwt_required()
def create_workout():
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if payload.keys() - WORKOUT_FIELDS:
        return _error("The workout contains unsupported fields.", 400)

    workout = Workout(user_id=user.id)
    error = _apply_fields(workout, payload, creating=True)
    if error:
        return _error(error, 400)
    db.session.add(workout)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while creating a workout.")
        return _error("Unable to create the workout right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Workout created successfully.",
            "workout": serialize_workout(workout),
        }
    ), 201


@workout_blueprint.get("")
@jwt_required()
def list_workouts():
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    try:
        workouts = db.session.scalars(
            db.select(Workout)
            .where(Workout.user_id == user.id)
            .order_by(Workout.workout_date.desc(), Workout.id.desc())
        ).all()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while retrieving workouts.")
        return _error("Unable to retrieve workouts right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Workouts retrieved successfully.",
            "workouts": [serialize_workout(item) for item in workouts],
        }
    ), 200


@workout_blueprint.get("/<int:workout_id>")
@jwt_required()
def get_workout(workout_id: int):
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    workout = db.session.scalar(
        db.select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == user.id,
        )
    )
    if workout is None:
        return _error("Workout not found.", 404)
    return jsonify(
        {"success": True, "workout": serialize_workout(workout)}
    ), 200


@workout_blueprint.put("/<int:workout_id>")
@jwt_required()
def update_workout(workout_id: int):
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    payload = _payload()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload:
        return _error("Provide at least one workout field to update.", 400)
    if payload.keys() - WORKOUT_FIELDS:
        return _error("The workout contains unsupported fields.", 400)

    workout = db.session.scalar(
        db.select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == user.id,
        )
    )
    if workout is None:
        return _error("Workout not found.", 404)
    error = _apply_fields(workout, payload)
    if error:
        return _error(error, 400)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating a workout.")
        return _error("Unable to update the workout right now.", 503)
    return jsonify(
        {
            "success": True,
            "message": "Workout updated successfully.",
            "workout": serialize_workout(workout),
        }
    ), 200


@workout_blueprint.delete("/<int:workout_id>")
@jwt_required()
def delete_workout(workout_id: int):
    user = _member()
    if user is None:
        return _error("A valid member account is required.", 403)
    workout = db.session.scalar(
        db.select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == user.id,
        )
    )
    if workout is None:
        return _error("Workout not found.", 404)
    try:
        db.session.delete(workout)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while deleting a workout.")
        return _error("Unable to delete the workout right now.", 503)
    return jsonify({"success": True, "message": "Workout deleted successfully."}), 200
