import unittest
from datetime import date, timedelta
from decimal import Decimal

from app import create_app
from extensions import db
from membership_plans import MEMBERSHIP_DURATIONS, MEMBERSHIP_PLANS
from models import Membership, User
from werkzeug.security import generate_password_hash


class TestMembershipApi(unittest.TestCase):
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
        self.member = User(
            name="Test Member",
            email="member@example.com",
            phone="+1 555 123 4567",
            password_hash=generate_password_hash("MemberPass123!"),
            role="member",
        )
        self.admin = User(
            name="Test Admin",
            email="admin@example.com",
            phone="+1 555 765 4321",
            password_hash=generate_password_hash("AdminPass123!"),
            role="admin",
        )
        db.session.add_all([self.member, self.admin])
        db.session.commit()
        self.member_token = self.login("member@example.com", "MemberPass123!")
        self.admin_token = self.login("admin@example.com", "AdminPass123!")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

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

    def create_membership(self, **overrides):
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

    def test_plans_list_configured_plan_prices_and_durations(self):
        response = self.client.get("/api/membership/plans")

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(
            {plan["plan_type"] for plan in body["plans"]},
            set(MEMBERSHIP_PLANS),
        )
        self.assertTrue(
            all(plan["durations_months"] == list(MEMBERSHIP_DURATIONS) for plan in body["plans"])
        )
        pro = next(plan for plan in body["plans"] if plan["plan_type"] == "pro")
        self.assertEqual(pro["prices"], {"1": 1500, "3": 4500, "6": 9000})

    def test_member_endpoints_require_authentication(self):
        current = self.client.get("/api/membership/current")
        history = self.client.get("/api/membership/history")

        self.assertEqual(current.status_code, 401)
        self.assertEqual(history.status_code, 401)
        self.assertFalse(current.get_json()["success"])

    def test_current_membership_returns_dates_status_and_remaining_days(self):
        membership = self.create_membership(
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=10),
        )

        response = self.client.get(
            "/api/membership/current",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()["membership"]
        self.assertEqual(result["id"], membership.id)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["remaining_days"], 10)
        self.assertEqual(result["start_date"], membership.start_date.isoformat())
        self.assertEqual(result["end_date"], membership.end_date.isoformat())

    def test_membership_is_active_through_its_end_date(self):
        self.create_membership(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        response = self.client.get(
            "/api/membership/current",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["membership"]["status"], "active")
        self.assertEqual(response.get_json()["membership"]["remaining_days"], 0)

    def test_expired_membership_is_not_current_and_history_updates_status(self):
        membership = self.create_membership(
            start_date=date.today() - timedelta(days=31),
            end_date=date.today() - timedelta(days=1),
        )

        current = self.client.get(
            "/api/membership/current",
            headers=self.auth(self.member_token),
        )
        history = self.client.get(
            "/api/membership/history",
            headers=self.auth(self.member_token),
        )

        self.assertIsNone(current.get_json()["membership"])
        self.assertEqual(history.get_json()["memberships"][0]["status"], "expired")
        self.assertEqual(db.session.get(Membership, membership.id).status, "expired")

    def test_history_is_newest_first_and_scoped_to_authenticated_user(self):
        old = self.create_membership(
            start_date=date.today() - timedelta(days=90),
            end_date=date.today() - timedelta(days=60),
            status="expired",
        )
        new = self.create_membership(
            plan_name="PRO",
            plan_type="pro",
            price=Decimal("1500.00"),
        )

        response = self.client.get(
            "/api/membership/history",
            headers=self.auth(self.member_token),
        )
        items = response.get_json()["memberships"]

        self.assertEqual([item["id"] for item in items], [new.id, old.id])
        self.assertEqual(items[1]["status"], "expired")

        other_member = User(
            name="Other Member",
            email="other@example.com",
            phone="+1 555 000 1111",
            password_hash=generate_password_hash("OtherPass123!"),
            role="member",
        )
        db.session.add(other_member)
        db.session.flush()
        self.create_membership(user_id=other_member.id)
        own_history = self.client.get(
            "/api/membership/history",
            headers=self.auth(self.member_token),
        ).get_json()["memberships"]
        self.assertEqual({item["id"] for item in own_history}, {new.id, old.id})

    def test_member_cannot_access_admin_routes(self):
        response = self.client.get(
            "/api/admin/memberships",
            headers=self.auth(self.member_token),
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_endpoints_require_admin_token(self):
        missing = self.client.get("/api/admin/memberships")
        member = self.client.post(
            "/api/admin/memberships",
            headers=self.auth(self.member_token),
            json={"user_id": self.member.id, "plan_type": "basic", "duration_months": 1},
        )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(member.status_code, 403)

    def test_admin_assigns_membership_and_rejects_second_active_assignment(self):
        payload = {
            "user_id": self.member.id,
            "plan_type": "pro",
            "duration_months": 3,
        }
        response = self.client.post(
            "/api/admin/memberships",
            headers=self.auth(self.admin_token),
            json=payload,
        )

        self.assertEqual(response.status_code, 201)
        membership = response.get_json()["membership"]
        self.assertEqual(membership["plan_name"], "PRO")
        self.assertEqual(membership["price"], 4500.0)
        self.assertEqual(membership["status"], "active")

        duplicate = self.client.post(
            "/api/admin/memberships",
            headers=self.auth(self.admin_token),
            json=payload,
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_admin_list_update_renew_and_cancel(self):
        membership = self.create_membership()
        headers = self.auth(self.admin_token)

        listing = self.client.get("/api/admin/memberships", headers=headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.get_json()["memberships"]), 1)

        update = self.client.put(
            f"/api/admin/memberships/{membership.id}",
            headers=headers,
            json={"plan_type": "elite", "duration_months": 3},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["membership"]["plan_type"], "elite")
        self.assertEqual(update.get_json()["membership"]["price"], 7500.0)

        previous_end = membership.end_date
        renew = self.client.post(
            f"/api/admin/memberships/{membership.id}/renew",
            headers=headers,
            json={"duration_months": 1},
        )
        self.assertEqual(renew.status_code, 200)
        renewed = renew.get_json()["membership"]
        self.assertEqual(renewed["end_date"], (previous_end + timedelta(days=31)).isoformat())
        self.assertEqual(renewed["price"], 10000.0)

        cancel = self.client.delete(
            f"/api/admin/memberships/{membership.id}",
            headers=headers,
        )
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(cancel.get_json()["membership"]["status"], "cancelled")

    def test_admin_validates_assignment_fields_and_member_role(self):
        invalid_plan = self.client.post(
            "/api/admin/memberships",
            headers=self.auth(self.admin_token),
            json={"user_id": self.member.id, "plan_type": "gold", "duration_months": 1},
        )
        admin_assignment = self.client.post(
            "/api/admin/memberships",
            headers=self.auth(self.admin_token),
            json={"user_id": self.admin.id, "plan_type": "basic", "duration_months": 1},
        )

        self.assertEqual(invalid_plan.status_code, 400)
        self.assertEqual(admin_assignment.status_code, 400)

    def test_model_relationship_connects_user_and_memberships(self):
        membership = self.create_membership()

        self.assertEqual(self.member.memberships[0].id, membership.id)
        self.assertEqual(membership.user.id, self.member.id)


if __name__ == "__main__":
    unittest.main()
