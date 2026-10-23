import os

import click
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from models import Attendance, Membership, Notification, Payment, Progress, User, Workout
from routes import (
    admin_membership_blueprint,
    api_blueprint,
    admin_attendance_blueprint,
    admin_announcement_blueprint,
    admin_dashboard_blueprint,
    admin_member_blueprint,
    admin_plan_blueprint,
    auth_blueprint,
    attendance_blueprint,
    dashboard_blueprint,
    membership_blueprint,
    progress_blueprint,
    workout_blueprint,
)
from utils.auth_validation import validate_email, validate_phone
from utils.bootstrap import seed_membership_plans


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config.setdefault("MAX_CONTENT_LENGTH", 1_048_576)

    db.init_app(app)
    jwt = JWTManager(app)
    jwt.unauthorized_loader(
        lambda _reason: (
            {"success": False, "message": "Authorization token is required."},
            401,
        )
    )
    jwt.invalid_token_loader(
        lambda _reason: (
            {"success": False, "message": "The authorization token is invalid."},
            401,
        )
    )
    jwt.expired_token_loader(
        lambda _jwt_header, _jwt_payload: (
            {"success": False, "message": "The authorization token has expired."},
            401,
        )
    )
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
    )
    app.register_blueprint(api_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(membership_blueprint)
    app.register_blueprint(admin_membership_blueprint)
    app.register_blueprint(attendance_blueprint)
    app.register_blueprint(admin_attendance_blueprint)
    app.register_blueprint(admin_member_blueprint)
    app.register_blueprint(admin_plan_blueprint)
    app.register_blueprint(admin_dashboard_blueprint)
    app.register_blueprint(admin_announcement_blueprint)
    app.register_blueprint(workout_blueprint)
    app.register_blueprint(progress_blueprint)
    app.register_blueprint(dashboard_blueprint)

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        db.session.rollback()
        app.logger.error(
            "Database operation failed.",
            exc_info=(type(error), error, error.__traceback__),
        )
        return {
            "success": False,
            "message": "Database service is temporarily unavailable.",
        }, 503

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(_error):
        return {
            "success": False,
            "message": "Request body must not exceed 1 MB.",
        }, 413

    @app.cli.command("create-admin")
    def create_admin():
        """Create an administrator interactively; public registration cannot assign this role."""
        name = click.prompt("Full name").strip()
        email = validate_email(click.prompt("Email address"))
        phone = validate_phone(click.prompt("Phone number"))
        password = click.prompt(
            "Password",
            hide_input=True,
            confirmation_prompt=True,
        )

        if not name or len(name) > 120:
            raise click.ClickException("Name must be between 1 and 120 characters.")
        if email is None:
            raise click.ClickException("Enter a valid email address.")
        if phone is None:
            raise click.ClickException("Enter a valid phone number with at least 7 digits.")
        if len(password) < 8 or len(password) > 128:
            raise click.ClickException("Password must be between 8 and 128 characters.")
        if db.session.scalar(db.select(User.id).where(User.email == email)) is not None:
            raise click.ClickException("An account with this email already exists.")

        admin = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role="admin",
        )
        db.session.add(admin)
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise click.ClickException("An account with this email already exists.") from error

        click.echo(f"Administrator account created for {email}.")

    @app.cli.command("seed-membership-plans")
    def seed_plans():
        """Insert default plans that are missing from the database."""
        try:
            added = seed_membership_plans()
        except SQLAlchemyError as error:
            db.session.rollback()
            raise click.ClickException("Unable to seed membership plans.") from error
        click.echo(f"Added {added} default membership plan(s).")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
