from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from vehicles.models import Vehicle, Brand
from http import HTTPStatus
import json
from django.middleware.csrf import get_token
from django.http import HttpRequest


class VehiclesCSRFTest(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

        User = get_user_model()
        self.user = User.objects.create_user(
            username='manager_3',
            password='12345678asd',
            is_staff=True
        )

        self.client.login(username='manager_3', password='12345678asd')

        self.brand = Brand.objects.create(
            product_name='TestBrand',
            fuel_tank_capacity=50,
            country_of_origin='TestCountry',
            car_class='A',
            maximum_load_kg=1000,
            number_of_passengers=4
        )

    def test_get_csrf_token_directly(self):
        request = HttpRequest()
        request.method = 'GET'
        print(get_token(request))

    def test_csrf_protection_works(self):
        response = self.client.post(
            '/api/v1/vehicles/',
            data=json.dumps({
                "plate_number": "X999XX178",
                "prod_date": "2025-01-01",
                "odometer": 0,
                "price": 1000000,
                "color": "Синий",
                "brand": self.brand.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_csrf_with_wrong_token(self):
        response = self.client.post(
            '/api/v1/vehicles/',
            data=json.dumps({
                "plate_number": "Z999ZZ178",
                "prod_date": "2025-01-01",
                "odometer": 0,
                "price": 1000000,
                "color": "Зеленый",
                "brand": self.brand.id
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN='WRONG_TOKEN_123'
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_request_works(self):
        response = self.client.get('/api/v1/vehicles/')
        self.assertEqual(response.status_code, HTTPStatus.OK)