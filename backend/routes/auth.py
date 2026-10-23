import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import User
from utils.auth_validation import (
    ALLOWED_GENDERS,
    validate_date_of_birth,
    validate_email,
    validate_phone,
    validate_profile_photo,
)


auth_blueprint = Blueprint("auth", __name__, url_prefix="/api/auth")
logger = logging.getLogger(__name__)
REGISTER_FIELDS = {"name", "email", "phone", "password"}
PROFILE_FIELDS = {"name", "phone", "fitness_goal", "date_of_birth", "gender", "profile_photo"}


def _error(message: str, status_code: int):
    return jsonify({"success": False, "message": message}), status_code


def _json_object():
    if not request.is_json:
        return None
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else None


def _serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "fitness_goal": user.fitness_goal,
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "gender": user.gender,
        "profile_photo": user.profile_photo,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def _authenticated_user():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return None
    user = db.session.get(User, user_id)
    return user if user and user.is_active else None


@auth_blueprint.post("/register")
def register():
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)

    unknown_fields = payload.keys() - REGISTER_FIELDS
    if unknown_fields:
        return _error(
            f"Unsupported registration field(s): {', '.join(sorted(unknown_fields))}.",
            400,
        )
    missing_fields = REGISTER_FIELDS - payload.keys()
    if missing_fields:
        return _error(
            f"Missing required field(s): {', '.join(sorted(missing_fields))}.",
            400,
        )

    name = payload["name"]
    password = payload["password"]
    email = validate_email(payload["email"])
    phone = validate_phone(payload["phone"])

    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        return _error("Name must be between 1 and 120 characters.", 400)
    if email is None:
        return _error("Enter a valid email address.", 400)
    if phone is None:
        return _error("Enter a valid phone number with at least 7 digits.", 400)
    if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
        return _error("Password must be between 8 and 128 characters.", 400)

    if db.session.scalar(db.select(User.id).where(User.email == email)) is not None:
        return _error("An account with this email already exists.", 409)

    user = User(
        name=name.strip(),
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role="member",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("An account with this email already exists.", 409)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while registering a member.")
        return _error("Unable to create the account right now.", 500)

    return jsonify(
        {
            "success": True,
            "message": "Registration successful",
            "user": _serialize_user(user),
        }
    ), 201


@auth_blueprint.post("/login")
def login():
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if payload.keys() - {"email", "password"}:
        return _error("Only email and password are accepted.", 400)
    if "email" not in payload or "password" not in payload:
        return _error("Email and password are required.", 400)

    email = validate_email(payload["email"])
    password = payload["password"]
    if email is None or not isinstance(password, str) or len(password) > 128:
        return _error("Invalid email or password.", 401)

    user = db.session.scalar(db.select(User).where(User.email == email))
    if (
        user is None
        or not user.is_active
        or not check_password_hash(user.password_hash, password)
    ):
        return _error("Invalid email or password.", 401)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role},
    )
    return jsonify(
        {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": _serialize_user(user),
        }
    ), 200


@auth_blueprint.get("/me")
@jwt_required()
def get_profile():
    user = _authenticated_user()
    if user is None:
        return _error("The account for this token no longer exists.", 401)
    return jsonify(
        {
            "success": True,
            "message": "Profile retrieved successfully",
            "user": _serialize_user(user),
        }
    ), 200


@auth_blueprint.put("/profile")
@jwt_required()
def update_profile():
    payload = _json_object()
    if payload is None:
        return _error("A JSON request body is required.", 400)
    if not payload:
        return _error("Provide at least one profile field to update.", 400)

    unsupported_fields = payload.keys() - PROFILE_FIELDS
    if unsupported_fields:
        return _error(
            f"Unsupported profile field(s): {', '.join(sorted(unsupported_fields))}.",
            400,
        )

    user = _authenticated_user()
    if user is None:
        return _error("The account for this token no longer exists.", 401)

    updates = {}
    if "name" in payload:
        name = payload["name"]
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            return _error("Name must be between 1 and 120 characters.", 400)
        updates["name"] = name.strip()

    if "phone" in payload:
        phone_value = payload["phone"]
        if phone_value is None:
            updates["phone"] = None
        else:
            phone = validate_phone(phone_value)
            if phone is None:
                return _error("Enter a valid phone number with at least 7 digits.", 400)
            updates["phone"] = phone

    if "fitness_goal" in payload:
        goal = payload["fitness_goal"]
        if goal is not None and (
            not isinstance(goal, str) or not goal.strip() or len(goal.strip()) > 80
        ):
            return _error("Fitness goal must be between 1 and 80 characters.", 400)
        updates["fitness_goal"] = goal.strip() if isinstance(goal, str) else None

    if "date_of_birth" in payload:
        value = payload["date_of_birth"]
        if value is None:
            updates["date_of_birth"] = None
        else:
            birth_date = validate_date_of_birth(value)
            if birth_date is None:
                return _error("Date of birth must be a valid past date in YYYY-MM-DD format.", 400)
            updates["date_of_birth"] = birth_date

    if "gender" in payload:
        gender = payload["gender"]
        if gender is None:
            updates["gender"] = None
        elif not isinstance(gender, str) or gender.strip().lower() not in ALLOWED_GENDERS:
            return _error(
                "Gender must be male, female, non-binary, other, or prefer_not_to_say.",
                400,
            )
        else:
            updates["gender"] = gender.strip().lower()

    if "profile_photo" in payload:
        photo = payload["profile_photo"]
        if photo is None:
            updates["profile_photo"] = None
        else:
            validated_photo = validate_profile_photo(photo)
            if validated_photo is None:
                return _error("Profile photo must be an absolute HTTP or HTTPS URL.", 400)
            updates["profile_photo"] = validated_photo

    for field, value in updates.items():
        setattr(user, field, value)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database error while updating a member profile.")
        return _error("Unable to update the profile right now.", 500)

    return jsonify(
        {
            "success": True,
            "message": "Profile updated successfully",
            "user": _serialize_user(user),
        }
    ), 200
