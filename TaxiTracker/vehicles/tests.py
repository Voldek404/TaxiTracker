from django.test import SimpleTestCase, Client
from http import HTTPStatus

class VehiclesApiViewTestCase(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_create_vehicle_wrong_token(self):
        response = self.client.post(
            "/api/v1/vehicles/",
            {
                "plate_number": "X999XX178",
                "prod_date": "2025-01-01",
                "odometer": 0,
                "price": 1000000,
                "color": "Синий",
                "brand": 1,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN="WRONGTOKEN",
        )
        print(response.status_code)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
