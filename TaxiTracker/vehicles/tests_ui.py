from django_webtest import WebTest
from django.contrib.auth import get_user_model

from .models import Enterprise, Manager


class DashboardUITest(WebTest):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="user",
            password="12345678asd",
            is_staff=True,
        )

        self.manager = Manager.objects.create(
            user=self.user
        )

        self.enterprise = Enterprise.objects.create(
            name="TestEnterprise",
            city="TestCity",
        )

        self.enterprise.managers.set(
            [self.manager]
        )


    def test_login_page(self):

        page = self.app.get(
            "/login/"
        )

        self.assertEqual(
            page.status_code,
            200
        )

        self.assertIn(
            "Авторизация в системе Таксопарка",
            page.text
        )

    def test_login_success(self):
        page = self.app.get(
            "/login/"
        )

        form = page.forms[0]

        form["username"] = "user"
        form["password"] = "12345678asd"

        response = form.submit()

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            "/dashboard/",
            response.location
        )

    def test_dashboard_contains_enterprise(self):
        login = self.app.get("/login/")

        form = login.forms[0]

        form["username"] = "user"
        form["password"] = "12345678asd"

        form.submit()

        page = self.app.get(
            "/dashboard/"
        )

        self.assertIn(
            "TestEnterprise",
            page.text
        )

    def test_login_redirects_to_dashboard(self):
        page = self.app.get("/login/")

        form = page.forms[0]
        form["username"] = "user"
        form["password"] = "12345678asd"

        response = form.submit()

        self.assertEqual(response.status_code, 302)

        dashboard = response.follow()

        self.assertEqual(
            dashboard.status_code,
            200
        )

        self.assertIn(
            "TestEnterprise",
            dashboard.text
        )

    def test_dashboard_requires_login(self):
        response = self.app.get(
            "/dashboard/"
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            "/login/",
            response.location
        )

