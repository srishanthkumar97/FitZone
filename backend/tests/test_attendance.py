import unittest
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from models import Attendance, Membership, User
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash


class TestAttendanceApi(unittest.TestCase):
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
        self.admin = self.create_user("admin@example.com", "admin")
        self.member_token = self.login("member@example.com", "MemberPass123!")
        self.admin_token = self.login("admin@example.com", "MemberPass123!")

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

    def login(self, email, password):
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200)
        return response.get_json()["token"]

    @staticmethod
    def auth(token):
        return {"Authorization": f"Bearer {token}"}

    def add_membership(self, **overrides):
        today = date.today()
        values = {
            "user_id": self.member.id,
            "plan_name": "BASIC",
            "plan_type": "basic",
            "price": Decimal("1200.00"),
            "start_date": today,
            "end_date": today + timedelta(days=30),
            "status": "active",
        }
        values.update(overrides)
        membership = Membership(**values)
        db.session.add(membership)
        db.session.commit()
        return membership

    def add_attendance(self, user_id, attended_on):
        record = Attendance(
            user_id=user_id,
            attendance_date=attended_on,
            check_in_time=datetime.combine(attended_on, time(9)),
            check_out_time=datetime.combine(attended_on, time(10)),
            status="checked_out",
        )
        db.session.add(record)
        db.session.commit()
        return record

    def test_check_in_requires_authentication_and_active_membership(self):
        unauthorized = self.client.post("/api/attendance/check-in")
        no_membership = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(no_membership.status_code, 403)
        self.assertIn("active membership", no_membership.get_json()["message"])

    def test_valid_check_in_and_duplicate_check_in(self):
        self.add_membership()

        response = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["attendance"]["attendance_date"], date.today().isoformat())
        self.assertEqual(body["attendance"]["status"], "checked_in")
        self.assertIsNotNone(body["attendance"]["check_in_time"])
        self.assertEqual(body["current_streak"], 1)

        duplicate = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_expired_membership_cannot_check_in(self):
        self.add_membership(
            start_date=date.today() - timedelta(days=31),
            end_date=date.today() - timedelta(days=1),
        )

        response = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("membership has expired", response.get_json()["message"])

    def test_checkout_requires_check_in_and_records_time(self):
        invalid = self.client.post(
            "/api/attendance/check-out",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(invalid.status_code, 404)

        self.add_membership()
        checked_in = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )
        attendance_id = checked_in.get_json()["attendance"]["id"]
        checkout = self.client.post(
            "/api/attendance/check-out",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(checkout.status_code, 200)
        self.assertEqual(checkout.get_json()["attendance"]["id"], attendance_id)
        self.assertEqual(checkout.get_json()["attendance"]["status"], "checked_out")
        self.assertIsNotNone(checkout.get_json()["attendance"]["check_out_time"])

    def test_history_filters_and_only_returns_authenticated_member_records(self):
        today = date.today()
        current = self.add_attendance(self.member.id, today)
        old_date = today - timedelta(days=400)
        old = self.add_attendance(self.member.id, old_date)
        self.add_attendance(self.admin.id, today)

        all_records = self.client.get(
            "/api/attendance/history",
            headers=self.auth(self.member_token),
        )
        filtered = self.client.get(
            f"/api/attendance/history?month={today.month}&year={today.year}",
            headers=self.auth(self.member_token),
        )
        invalid_filter = self.client.get(
            "/api/attendance/history?month=13",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(all_records.status_code, 200)
        self.assertEqual(
            {item["id"] for item in all_records.get_json()["attendance"]},
            {current.id, old.id},
        )
        self.assertEqual(
            [item["id"] for item in filtered.get_json()["attendance"]],
            [current.id],
        )
        self.assertEqual(invalid_filter.status_code, 400)

    def test_summary_calculates_current_and_longest_streak(self):
        today = date.today()
        for offset in range(12, 6, -1):
            self.add_attendance(self.member.id, today - timedelta(days=offset))
        for offset in range(2, -1, -1):
            self.add_attendance(self.member.id, today - timedelta(days=offset))

        response = self.client.get(
            "/api/attendance/summary",
            headers=self.auth(self.member_token),
        )

        summary = response.get_json()["summary"]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(summary["total_attendance_days"], 9)
        self.assertEqual(summary["current_streak"], 3)
        self.assertEqual(summary["longest_streak"], 6)
        self.assertEqual(summary["last_attendance_date"], today.isoformat())
        self.assertEqual(
            summary["current_month_attendance"],
            sum(
                (today - timedelta(days=offset)).month == today.month
                for offset in list(range(12, 6, -1)) + list(range(2, -1, -1))
            ),
        )

    def test_current_streak_resets_after_missing_more_than_one_day(self):
        today = date.today()
        self.add_attendance(self.member.id, today - timedelta(days=3))

        response = self.client.get(
            "/api/attendance/summary",
            headers=self.auth(self.member_token),
        )

        summary = response.get_json()["summary"]
        self.assertEqual(summary["current_streak"], 0)
        self.assertEqual(summary["longest_streak"], 1)

    def test_admin_attendance_endpoints_are_role_protected(self):
        member_access = self.client.get(
            "/api/admin/attendance/today",
            headers=self.auth(self.member_token),
        )
        self.assertEqual(member_access.status_code, 403)

        self.add_attendance(self.member.id, date.today())
        headers = self.auth(self.admin_token)
        today = self.client.get("/api/admin/attendance/today", headers=headers)
        member_history = self.client.get(
            f"/api/admin/attendance/members/{self.member.id}",
            headers=headers,
        )
        stats = self.client.get(
            "/api/admin/attendance/statistics",
            headers=headers,
        )

        self.assertEqual(today.status_code, 200)
        self.assertEqual(len(today.get_json()["attendance"]), 1)
        self.assertEqual(member_history.status_code, 200)
        self.assertEqual(len(member_history.get_json()["attendance"]), 1)
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.get_json()["statistics"]["today_attendance"], 1)

    def test_model_relationship_and_database_daily_uniqueness(self):
        self.add_membership()
        response = self.client.post(
            "/api/attendance/check-in",
            headers=self.auth(self.member_token),
        )
        attendance_id = response.get_json()["attendance"]["id"]
        record = db.session.get(Attendance, attendance_id)

        self.assertEqual(record.user.id, self.member.id)
        self.assertEqual(self.member.attendance_records[0].id, attendance_id)

        duplicate = Attendance(
            user_id=self.member.id,
            attendance_date=date.today(),
            check_in_time=datetime.now(),
        )
        db.session.add(duplicate)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()


if __name__ == "__main__":
    unittest.main()
