import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from models import Attendance, Membership, Progress, User, Workout
from werkzeug.security import generate_password_hash


class TestWorkoutsProgressApi(unittest.TestCase):
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
        self.member = self.create_user("member@example.com", "member")
        self.other_member = self.create_user("other@example.com", "member")
        self.admin = self.create_user("admin@example.com", "admin")
        self.member_token = self.login("member@example.com")
        self.other_token = self.login("other@example.com")
        self.admin_token = self.login("admin@example.com")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def create_user(self, email, role):
        user = User(
            name="Test User",
            email=email,
            phone="+1 555 123 4567",
            password_hash=generate_password_hash("MemberPass123!"),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return user

    def login(self, email):
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": "MemberPass123!"},
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()["token"]

    @staticmethod
    def auth(token):
        return {"Authorization": f"Bearer {token}"}

    def create_workout(self, token=None, **values):
        payload = {
            "workout_type": "Strength",
            "duration": 60,
            "exercises": [
                {
                    "exercise_name": "Squat",
                    "sets": 4,
                    "reps": 8,
                    "weight": 80,
                }
            ],
        }
        payload.update(values)
        return self.client.post(
            "/api/workouts",
            headers=self.auth(token or self.member_token),
            json=payload,
        )

    def test_workout_crud_and_exercise_replacement(self):
        created = self.create_workout()
        self.assertEqual(created.status_code, 201)
        body = created.get_json()["workout"]
        self.assertEqual(body["user_id"], self.member.id)
        self.assertEqual(body["workout_date"], date.today().isoformat())
        self.assertEqual(body["exercises"][0]["exercise_name"], "Squat")

        workout_id = body["id"]
        listing = self.client.get(
            "/api/workouts",
            headers=self.auth(self.member_token),
        )
        detail = self.client.get(
            f"/api/workouts/{workout_id}",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()["workouts"]), 1)
        self.assertEqual(detail.get_json()["workout"]["id"], workout_id)

        updated = self.client.put(
            f"/api/workouts/{workout_id}",
            headers=self.auth(self.member_token),
            json={
                "duration": 75,
                "exercises": [{"exercise_name": "Bench press", "sets": 3}],
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["workout"]["duration"], 75)
        self.assertEqual(
            updated.get_json()["workout"]["exercises"][0]["exercise_name"],
            "Bench press",
        )
        self.assertEqual(len(db.session.get(Workout, workout_id).exercises), 1)

        deleted = self.client.delete(
            f"/api/workouts/{workout_id}",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertIsNone(db.session.get(Workout, workout_id))

    def test_workouts_are_private_and_admin_cannot_modify_member_workouts(self):
        workout_id = self.create_workout().get_json()["workout"]["id"]

        other_member = self.client.get(
            f"/api/workouts/{workout_id}",
            headers=self.auth(self.other_token),
        )
        admin = self.client.put(
            f"/api/workouts/{workout_id}",
            headers=self.auth(self.admin_token),
            json={"duration": 20},
        )

        self.assertEqual(other_member.status_code, 404)
        self.assertEqual(admin.status_code, 403)
        self.assertEqual(db.session.get(Workout, workout_id).duration, 60)

    def test_workout_validation_and_authentication(self):
        unauthorized = self.client.post(
            "/api/workouts",
            json={"workout_type": "Strength", "duration": 30},
        )
        invalid = self.create_workout(duration=0)
        malformed_exercise = self.create_workout(
            exercises=[{"exercise_name": "", "sets": 0}]
        )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(malformed_exercise.status_code, 400)

    def test_progress_create_history_latest_and_private_scope(self):
        yesterday = date.today() - timedelta(days=1)
        older = self.client.post(
            "/api/progress",
            headers=self.auth(self.member_token),
            json={"record_date": yesterday.isoformat(), "weight": 82.5},
        )
        latest = self.client.post(
            "/api/progress",
            headers=self.auth(self.member_token),
            json={"weight": 81.2, "body_fat": 18.5, "notes": "Feeling strong"},
        )
        self.client.post(
            "/api/progress",
            headers=self.auth(self.other_token),
            json={"weight": 70},
        )

        self.assertEqual(older.status_code, 201)
        self.assertEqual(latest.status_code, 201)
        self.assertIsNone(latest.get_json()["progress"]["height"])

        history = self.client.get(
            "/api/progress",
            headers=self.auth(self.member_token),
        )
        latest_response = self.client.get(
            "/api/progress/latest",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.get_json()["progress"]), 2)
        self.assertEqual(
            history.get_json()["progress"][0]["id"],
            latest.get_json()["progress"]["id"],
        )
        self.assertEqual(
            latest_response.get_json()["progress"]["weight"],
            81.2,
        )

    def test_progress_validates_fields_and_requires_values(self):
        empty = self.client.post(
            "/api/progress",
            headers=self.auth(self.member_token),
            json={},
        )
        invalid = self.client.post(
            "/api/progress",
            headers=self.auth(self.member_token),
            json={"weight": -1},
        )
        invalid_body_fat = self.client.post(
            "/api/progress",
            headers=self.auth(self.member_token),
            json={"body_fat": 101},
        )

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid_body_fat.status_code, 400)

    def test_dashboard_combines_member_data(self):
        today = date.today()
        db.session.add(
            Membership(
                user_id=self.member.id,
                plan_name="PRO",
                plan_type="pro",
                price=Decimal("1500.00"),
                start_date=today - timedelta(days=5),
                end_date=today + timedelta(days=25),
                status="active",
            )
        )
        db.session.add(
            Attendance(
                user_id=self.member.id,
                attendance_date=today,
                check_in_time=datetime.now(),
                status="checked_in",
            )
        )
        db.session.add(
            Progress(
                user_id=self.member.id,
                record_date=today,
                weight=Decimal("80.50"),
            )
        )
        workout = Workout(
            user_id=self.member.id,
            workout_date=today,
            workout_type="Strength",
            duration=45,
        )
        db.session.add(workout)
        db.session.commit()

        response = self.client.get(
            "/api/dashboard",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["user"]["id"], self.member.id)
        self.assertEqual(body["membership"]["plan_type"], "pro")
        self.assertEqual(body["membership"]["remaining_days"], 25)
        self.assertEqual(body["attendance"]["current_streak"], 1)
        self.assertEqual(body["attendance"]["current_month_attendance"], 1)
        self.assertEqual(body["progress"]["weight"], 80.5)
        self.assertEqual(len(body["recent_workouts"]), 1)
        self.assertEqual(body["recent_notifications"], [])

    def test_dashboard_requires_member_token(self):
        missing = self.client.get("/api/dashboard")
        admin = self.client.get(
            "/api/dashboard",
            headers=self.auth(self.admin_token),
        )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(admin.status_code, 403)


if __name__ == "__main__":
    unittest.main()
