from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from vehicles.models import Vehicle, Brand, Enterprise, Driver, Manager
from http import HTTPStatus
import json
from django.middleware.csrf import get_token
from django.http import HttpRequest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission



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

        request = HttpRequest()
        self.csrf_token = get_token(request)
        self.client.cookies['csrftoken'] = self.csrf_token

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


class PutPostDeleteTestSuperuser(TestCase):
    def setUp(self):
        self.client = APIClient()  # DRF APIClient удобнее для JWT
        User = get_user_model()

        self.user = User.objects.create_superuser(
            username='superuser',
            password='12345678asd'
        )
        self.brand = Brand.objects.create(
            product_name='TestBrand',
            fuel_tank_capacity=50,
            country_of_origin='TestCountry',
            car_class='A',
            maximum_load_kg=1000,
            number_of_passengers=4
        )

        self.manager = Manager.objects.create(user=self.user)

        self.enterprise = Enterprise.objects.create(name="TestEnterprise")
        self.enterprise.managers.set([self.manager])

        self.vehicle = Vehicle.objects.create(
            plate_number="X000XX178",
            prod_date="2025-01-01",
            odometer=0,
            price=1000000,
            color="Белый",
            brand=self.brand,
            enterprise=self.enterprise
        )

        response = self.client.post(
            '/api/v1/token/',
            {'username': 'superuser', 'password': '12345678asd'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_post_creates_vehicle(self):
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
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_updates_vehicle(self):
        response = self.client.put(
            f'/api/v1/vehicles/{self.vehicle.id}/',
            data=json.dumps({
                "plate_number": "X111XX178",
                "prod_date": "2025-01-01",
                "odometer": 100,
                "price": 1200000,
                "color": "Красный",
                "brand": self.brand.id
            }),
            content_type='application/json'
        )
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_removes_vehicle(self):
        response = self.client.delete(f'/api/v1/vehicles/{self.vehicle.id}/')
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class PutPostDeleteTestUser(TestCase):
    def setUp(self):
        self.client = APIClient()  # удобнее для JWT
        User = get_user_model()

        # 1️⃣ Создаём обычного менеджера с is_staff=True
        self.user = User.objects.create_user(
            username='user',
            password='12345678asd',
            is_staff=True,
        )
        vehicle_ct = ContentType.objects.get_for_model(Vehicle)
        perms = Permission.objects.filter(content_type=vehicle_ct)
        self.user.user_permissions.set(perms)# 2️⃣ 
        self.manager = Manager.objects.create(user=self.user)

        self.enterprise = Enterprise.objects.create(name="TestEnterprise", city="TestCity")
        self.enterprise.managers.set([self.manager])  # ключевой момент

        self.brand = Brand.objects.create(
            product_name='TestBrand',
            fuel_tank_capacity=50,
            country_of_origin='TestCountry',
            car_class='A',
            maximum_load_kg=1000,
            number_of_passengers=4
        )

        self.vehicle = Vehicle.objects.create(
            plate_number="X000XX178",
            prod_date="2025-01-01",
            odometer=0,
            price=1000000,
            color="Белый",
            brand=self.brand,
            enterprise=self.enterprise
        )

        response = self.client.post(
            '/api/v1/token/',
            {'username': 'user', 'password': '12345678asd'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_post_creates_vehicle(self):
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
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_put_updates_vehicle(self):
        response = self.client.put(
            f'/api/v1/vehicles/{self.vehicle.id}/',
            data=json.dumps({
                "plate_number": "X111XX178",
                "prod_date": "2025-01-01",
                "odometer": 100,
                "price": 1200000,
                "color": "Красный",
                "brand": self.brand.id
            }),
            content_type='application/json'
        )
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_removes_vehicle(self):
        response = self.client.delete(f'/api/v1/vehicles/{self.vehicle.id}/')
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
