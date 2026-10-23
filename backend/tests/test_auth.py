import unittest
from datetime import date, timedelta

from app import create_app
from extensions import db
from models import User


class TestAuthApi(unittest.TestCase):
    def setUp(self):
        class TestConfig:
            TESTING = True
            SECRET_KEY = "test-secret-key-that-is-at-least-32-bytes"
            JWT_SECRET_KEY = "test-jwt-secret-that-is-at-least-32-bytes"
            JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
            SQLALCHEMY_DATABASE_URI = "sqlite://"
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            CORS_ORIGINS = ["http://localhost:5173"]

        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.registration = {
            "name": "Test Member",
            "email": "member@example.com",
            "phone": "+1 555 123 4567",
            "password": "StrongPass123!",
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def register(self, payload=None):
        return self.client.post(
            "/api/auth/register",
            json=payload if payload is not None else self.registration,
        )

    def login(self):
        return self.client.post(
            "/api/auth/login",
            json={
                "email": self.registration["email"],
                "password": self.registration["password"],
            },
        )

    def test_register_hashes_password_and_always_assigns_member(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["user"]["role"], "member")
        self.assertNotIn("password_hash", body["user"])
        user = db.session.scalar(
            db.select(User).where(User.email == "member@example.com")
        )
        self.assertNotEqual(user.password_hash, self.registration["password"])
        self.assertTrue(user.password_hash.startswith("scrypt:"))

    def test_duplicate_email_is_rejected(self):
        self.assertEqual(self.register().status_code, 201)
        response = self.register({**self.registration, "email": " MEMBER@EXAMPLE.COM "})

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.get_json()["success"])

    def test_invalid_registration_is_rejected(self):
        invalid_payload = {**self.registration, "email": "not-an-email"}
        response = self.register(invalid_payload)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_registration_cannot_assign_admin_role(self):
        response = self.register({**self.registration, "role": "admin"})

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(db.session.scalar(db.select(User.id)))

    def test_admin_is_created_only_by_separate_cli_command(self):
        result = self.app.test_cli_runner().invoke(
            args=["create-admin"],
            input=(
                "Gym Admin\n"
                "admin@example.com\n"
                "+1 555 111 2222\n"
                "AdminPass123!\n"
                "AdminPass123!\n"
            ),
        )

        self.assertEqual(result.exit_code, 0, result.output)
        admin = db.session.scalar(
            db.select(User).where(User.email == "admin@example.com")
        )
        self.assertEqual(admin.role, "admin")
        self.assertNotEqual(admin.password_hash, "AdminPass123!")

    def test_login_and_invalid_login(self):
        self.register()
        response = self.login()

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["message"], "Login successful")
        self.assertTrue(body["token"])
        self.assertNotIn("password_hash", body["user"])

        invalid = self.client.post(
            "/api/auth/login",
            json={"email": self.registration["email"], "password": "wrong"},
        )
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(invalid.get_json()["message"], "Invalid email or password.")

    def test_protected_profile_requires_token_and_returns_user_with_token(self):
        self.register()
        unauthorized = self.client.get("/api/auth/me")

        self.assertEqual(unauthorized.status_code, 401)
        self.assertFalse(unauthorized.get_json()["success"])

        token = self.login().get_json()["token"]
        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["user"]["email"], self.registration["email"])
        self.assertNotIn("password_hash", response.get_json()["user"])

        invalid_token = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        self.assertEqual(invalid_token.status_code, 401)
        self.assertFalse(invalid_token.get_json()["success"])

    def test_profile_update_validates_and_returns_updated_profile(self):
        self.register()
        token = self.login().get_json()["token"]
        response = self.client.put(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Member",
                "phone": "+1 555 987 6543",
                "fitness_goal": "Build strength",
                "date_of_birth": "1995-06-15",
                "gender": "prefer_not_to_say",
                "profile_photo": "https://example.com/member.jpg",
            },
        )

        self.assertEqual(response.status_code, 200)
        user = response.get_json()["user"]
        self.assertEqual(user["name"], "Updated Member")
        self.assertEqual(user["fitness_goal"], "Build strength")
        self.assertEqual(user["date_of_birth"], "1995-06-15")
        self.assertNotIn("password_hash", user)

    def test_invalid_profile_updates_are_rejected(self):
        self.register()
        token = self.login().get_json()["token"]
        future_date = (date.today() + timedelta(days=1)).isoformat()

        response = self.client.put(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"date_of_birth": future_date},
        )
        self.assertEqual(response.status_code, 400)

        forbidden = self.client.put(
            "/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"role": "admin"},
        )
        self.assertEqual(forbidden.status_code, 400)


if __name__ == "__main__":
    unittest.main()
