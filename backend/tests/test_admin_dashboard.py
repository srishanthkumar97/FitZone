import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from models import Attendance, Membership, MembershipPlan, Payment, User
from werkzeug.security import generate_password_hash


class TestAdminDashboardApi(unittest.TestCase):
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
        self.admin = self.create_user("admin@example.com", "admin")
        self.member = self.create_user("member@example.com", "member")
        self.admin_token = self.login(self.admin.email)
        self.member_token = self.login(self.member.email)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def create_user(self, email, role):
        user = User(
            name=email.split("@")[0].title(),
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

    def admin_headers(self):
        return self.auth(self.admin_token)

    def test_admin_guard_returns_401_or_403(self):
        no_token = self.client.get("/api/admin/members")
        member_token = self.client.get(
            "/api/admin/members",
            headers=self.auth(self.member_token),
        )
        admin_token = self.client.get(
            "/api/admin/members",
            headers=self.admin_headers(),
        )

        self.assertEqual(no_token.status_code, 401)
        self.assertEqual(member_token.status_code, 403)
        self.assertEqual(admin_token.status_code, 200)

    def test_admin_member_create_search_detail_update_and_deactivate(self):
        created = self.client.post(
            "/api/admin/members",
            headers=self.admin_headers(),
            json={
                "name": "New Member",
                "email": "new@example.com",
                "phone": "+1 555 222 3333",
                "password": "MemberPass123!",
            },
        )
        self.assertEqual(created.status_code, 201)
        member_id = created.get_json()["member"]["id"]
        listed = self.client.get(
            "/api/admin/members?search=new&status=active&membership=none",
            headers=self.admin_headers(),
        )
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.get_json()["pagination"]["total"], 1)
        self.assertEqual(listed.get_json()["members"][0]["email"], "new@example.com")

        update = self.client.put(
            f"/api/admin/members/{member_id}",
            headers=self.admin_headers(),
            json={"fitness_goal": "Strength"},
        )
        detail = self.client.get(
            f"/api/admin/members/{member_id}",
            headers=self.admin_headers(),
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["member"]["fitness_goal"], "Strength")
        self.assertNotIn("password_hash", detail.get_json()["member"])

        deleted = self.client.delete(
            f"/api/admin/members/{member_id}",
            headers=self.admin_headers(),
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(db.session.get(User, member_id).is_active)
        self.assertEqual(
            self.client.post(
                "/api/auth/login",
                json={"email": "new@example.com", "password": "MemberPass123!"},
            ).status_code,
            401,
        )

    def test_plan_management_and_membership_assignment_renewal(self):
        created = self.client.post(
            "/api/admin/membership-plans",
            headers=self.admin_headers(),
            json={
                "plan_type": "strength_plus",
                "name": "Strength Plus",
                "monthly_price": 2200,
                "durations_months": [1, 4, 6],
            },
        )
        self.assertEqual(created.status_code, 201)
        plan_id = created.get_json()["plan"]["id"]
        updated_plan = self.client.put(
            f"/api/admin/membership-plans/{plan_id}",
            headers=self.admin_headers(),
            json={"monthly_price": 2300},
        )
        self.assertEqual(updated_plan.status_code, 200)

        assignment = self.client.post(
            "/api/admin/memberships",
            headers=self.admin_headers(),
            json={
                "user_id": self.member.id,
                "plan_type": "strength_plus",
                "duration_months": 4,
            },
        )
        self.assertEqual(assignment.status_code, 201)
        membership = assignment.get_json()["membership"]
        self.assertEqual(membership["price"], 9200.0)
        renew = self.client.post(
            f"/api/admin/memberships/{membership['id']}/renew",
            headers=self.admin_headers(),
            json={"duration_months": 1},
        )
        self.assertEqual(renew.status_code, 200)

        deactivated = self.client.delete(
            f"/api/admin/membership-plans/{plan_id}",
            headers=self.admin_headers(),
        )
        self.assertEqual(deactivated.status_code, 200)
        no_longer_listed = self.client.get("/api/membership/plans")
        self.assertNotIn(
            "strength_plus",
            {item["plan_type"] for item in no_longer_listed.get_json()["plans"]},
        )

    def test_membership_plan_seed_command_is_idempotent(self):
        runner = self.app.test_cli_runner()
        first = runner.invoke(args=["seed-membership-plans"])
        second = runner.invoke(args=["seed-membership-plans"])

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertIn("Added 3", first.output)
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Added 0", second.output)
        self.assertEqual(
            len(db.session.scalars(db.select(MembershipPlan)).all()),
            3,
        )

    def test_admin_attendance_date_filters_and_member_lookup(self):
        today = date.today()
        membership = Membership(
            user_id=self.member.id,
            plan_name="BASIC",
            plan_type="basic",
            price=Decimal("1200.00"),
            start_date=today,
            end_date=today + timedelta(days=30),
            status="active",
        )
        db.session.add(membership)
        db.session.add(
            Attendance(
                user_id=self.member.id,
                attendance_date=today,
                check_in_time=datetime.now(),
                check_out_time=datetime.now(),
                status="checked_out",
            )
        )
        db.session.commit()

        monthly = self.client.get(
            f"/api/admin/attendance?month={today.month}&year={today.year}",
            headers=self.admin_headers(),
        )
        member = self.client.get(
            f"/api/admin/attendance/member/{self.member.id}",
            headers=self.admin_headers(),
        )
        invalid = self.client.get(
            "/api/admin/attendance?month=13&year=2026",
            headers=self.admin_headers(),
        )
        self.assertEqual(monthly.status_code, 200)
        self.assertEqual(len(monthly.get_json()["attendance"]), 1)
        self.assertEqual(member.status_code, 200)
        self.assertEqual(
            member.get_json()["attendance"][0]["status"],
            "checked_out",
        )
        self.assertEqual(invalid.status_code, 400)

    def test_dashboard_counts_membership_attendance_and_completed_revenue(self):
        today = date.today()
        month_start = today.replace(day=1)
        db.session.add_all(
            [
                Membership(
                    user_id=self.member.id,
                    plan_name="PRO",
                    plan_type="pro",
                    price=Decimal("1500.00"),
                    start_date=today - timedelta(days=4),
                    end_date=today + timedelta(days=3),
                    status="active",
                ),
                Attendance(
                    user_id=self.member.id,
                    attendance_date=today,
                    check_in_time=datetime.now(),
                    status="checked_in",
                ),
                Payment(
                    user_id=self.member.id,
                    amount=Decimal("1500.00"),
                    status="completed",
                    paid_at=datetime.combine(today, datetime.min.time()),
                ),
                Payment(
                    user_id=self.member.id,
                    amount=Decimal("900.00"),
                    status="pending",
                    paid_at=datetime.combine(today, datetime.min.time()),
                ),
            ]
        )
        db.session.commit()

        response = self.client.get(
            "/api/admin/dashboard",
            headers=self.admin_headers(),
        )
        custom = self.client.get(
            f"/api/admin/dashboard?start_date={month_start.isoformat()}&end_date={today.isoformat()}",
            headers=self.admin_headers(),
        )
        self.assertEqual(response.status_code, 200)
        stats = response.get_json()["statistics"]
        self.assertEqual(stats["total_members"], 1)
        self.assertEqual(stats["active_members"], 1)
        self.assertEqual(stats["today_attendance"], 1)
        self.assertEqual(stats["monthly_attendance"], 1)
        self.assertEqual(stats["members_expiring_soon"], 1)
        self.assertEqual(stats["total_revenue"], 1500.0)
        self.assertEqual(stats["monthly_revenue"], 1500.0)
        self.assertEqual(custom.get_json()["statistics"]["custom_period_revenue"], 1500.0)

    def test_announcement_create_update_list_delete(self):
        created = self.client.post(
            "/api/admin/announcements",
            headers=self.admin_headers(),
            json={"title": "Holiday Hours", "body": "The gym opens at 8 AM."},
        )
        self.assertEqual(created.status_code, 201)
        announcement_id = created.get_json()["announcement"]["id"]
        updated = self.client.put(
            f"/api/admin/announcements/{announcement_id}",
            headers=self.admin_headers(),
            json={"is_active": False},
        )
        listing = self.client.get(
            "/api/admin/announcements",
            headers=self.admin_headers(),
        )
        self.assertEqual(updated.status_code, 200)
        self.assertFalse(listing.get_json()["announcements"][0]["is_active"])
        deleted = self.client.delete(
            f"/api/admin/announcements/{announcement_id}",
            headers=self.admin_headers(),
        )
        self.assertEqual(deleted.status_code, 200)

    def test_member_detail_includes_safe_payment_history(self):
        db.session.add(
            Payment(
                user_id=self.member.id,
                amount=Decimal("1250.00"),
                status="completed",
                paid_at=datetime.now(),
                payment_method="card",
            )
        )
        db.session.commit()

        response = self.client.get(
            f"/api/admin/members/{self.member.id}",
            headers=self.admin_headers(),
        )

        self.assertEqual(response.status_code, 200)
        payment = response.get_json()["payments"][0]
        self.assertEqual(payment["amount"], 1250.0)
        self.assertNotIn("payment_method", payment)
        self.assertNotIn("transaction_id", payment)

    def test_deactivated_member_token_cannot_access_member_dashboard(self):
        deactivated = self.client.delete(
            f"/api/admin/members/{self.member.id}",
            headers=self.admin_headers(),
        )
        dashboard = self.client.get(
            "/api/dashboard",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(deactivated.status_code, 200)
        self.assertEqual(dashboard.status_code, 403)


if __name__ == "__main__":
    unittest.main()
