from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models import User


def admin_required(view):
    @wraps(view)
    @jwt_required()
    def wrapped(*args, **kwargs):
        try:
            user_id = int(get_jwt_identity())
        except (TypeError, ValueError):
            return jsonify(
                {"success": False, "message": "The account for this token no longer exists."}
            ), 401
        admin = db.session.get(User, user_id)
        if admin is None:
            return jsonify(
                {"success": False, "message": "The account for this token no longer exists."}
            ), 401
        if admin.role != "admin":
            return jsonify(
                {"success": False, "message": "Administrator access is required."}
            ), 403
        if not admin.is_active:
            return jsonify(
                {"success": False, "message": "This administrator account is deactivated."}
            ), 403
        return view(*args, **kwargs)

    return wrapped
