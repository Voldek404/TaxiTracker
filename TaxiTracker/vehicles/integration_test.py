from django_webtest import WebTest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

from .models import (
    Enterprise,
    Manager,
    Brand,
    Vehicle,
)


class FullIntegrationTest(WebTest):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="user",
            password="12345678asd",
            is_staff=True,
        )

        print(f"Создан пользователь: {self.user}")
        print("--------------------------")

        vehicle_ct = ContentType.objects.get_for_model(
            Vehicle
        )

        perms = Permission.objects.filter(
            content_type=vehicle_ct
        )

        self.user.user_permissions.set(perms)

        self.manager = Manager.objects.create(
            user=self.user
        )

        self.enterprise = Enterprise.objects.create(
            name="TestEnterprise",
            city="TestCity",
        )

        print(f"Создан автопарк: {self.enterprise}")
        print("--------------------------")

        self.enterprise.managers.set(
            [self.manager]
        )

        self.brand = Brand.objects.create(
            product_name="TestBrand",
            fuel_tank_capacity=50,
            country_of_origin="TestCountry",
            car_class="A",
            maximum_load_kg=1000,
            number_of_passengers=4,
        )

        self.api = APIClient()

        print(f"Создан бренд: {self.brand}")
        print("--------------------------")

    def test_full_integration_flow(self):

        login = self.app.get("/login/")

        form = login.forms[0]

        form["username"] = "user"
        form["password"] = "12345678asd"

        response = form.submit()

        self.assertEqual(
            response.status_code,
            302
        )

        dashboard = response.follow()

        self.assertEqual(
            dashboard.status_code,
            200
        )

        self.assertIn(
            "TestEnterprise",
            dashboard.text
        )


        response = self.api.post(
            "/api/v1/token/",
            {
                "username": "user",
                "password": "12345678asd",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        if response.status_code == status.HTTP_200_OK:
            print("Пользователь успешно авторизован")

        token = response.data["access"]

        self.api.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        if token:
            print("JWT токен успешно получен")

        response = self.api.post(
            "/api/v1/vehicles/",
            {
                "plate_number": "X999XX178",
                "prod_date": "2025-01-01",
                "odometer": 0,
                "price": 1000000,
                "color": "Синий",
                "brand": self.brand.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        vehicle = Vehicle.objects.get(
            plate_number="X999XX178"
        )

        response = self.api.put(
            f"/api/v1/vehicles/{vehicle.id}/",
            {
                "plate_number": "X111XX178",
                "prod_date": "2025-01-01",
                "odometer": 100,
                "price": 1200000,
                "color": "Красный",
                "brand": self.brand.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        vehicle.refresh_from_db()

        self.assertEqual(
            vehicle.plate_number,
            "X111XX178",
        )

        self.assertEqual(
            vehicle.odometer,
            100,
        )

        self.assertEqual(
            vehicle.color,
            "Красный",
        )

        response = self.api.delete(
            f"/api/v1/vehicles/{vehicle.id}/"
        )
        # only superuser can delete objects

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        if response.status_code == status.HTTP_403_FORBIDDEN:
            print("Только суперпользователь может удалять машины")


        self.assertTrue(
            Vehicle.objects.filter(
                id=vehicle.id
            ).exists()
        )