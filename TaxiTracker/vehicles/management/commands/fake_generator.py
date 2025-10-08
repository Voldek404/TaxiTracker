import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction
from vehicles.models import Vehicle, Driver, VehicleDriver, Brand


_ALLOWED_LETTERS = list("АВЕКМНОРСТУХ")
_REGION_CODES = [
    "77", "97", "99", "50", "90", "150",
    "78", "98", "23", "93", "61", "161",
    "52", "152", "66", "96", "196"
]


class Command(BaseCommand):
    help = "Генерация заданного количества авто с водителями для конкретного автопарка"

    def add_arguments(self, parser):
        parser.add_argument('enterprise_id', type=int, help="ID автопарка")
        parser.add_argument('number_of_cars', type=int, help="Количество машин для генерации")

    def generate_plate(self) -> str:
        l1 = random.choice(_ALLOWED_LETTERS)
        l2 = random.choice(_ALLOWED_LETTERS)
        l3 = random.choice(_ALLOWED_LETTERS)
        digits = f"{random.randint(0, 999):03d}"
        region = random.choice(_REGION_CODES)
        return f"{l1}{digits}{l2}{l3}{region}"

    def generate_vehicles(self, enterprise_id, number_of_cars, fake_ru, fake_en):
        vehicles = []
        for _ in range(number_of_cars):
            vehicle = {
                "prod_date": fake_ru.date_of_birth(),
                "odometer": fake_ru.random_int(30000, 200000),
                "price": fake_ru.random_int(30000, 200000),
                "color": random.choice([fake_ru.color_name(),fake_en.color_name()]),
                "plate_number": self.generate_plate(),
                "enterprise_id": enterprise_id,
                "brand": random.choice(Brand.objects.all()),
            }
            vehicles.append(vehicle)
        return vehicles

    def generate_drivers(self, enterprise_id, number_of_drivers, fake_ru):
        drivers = []
        for i in range(number_of_drivers):
            is_active = ((i + 1) % 10 == 0)
            driver = {
                "full_name": fake_ru.name(),
                "salary": fake_ru.random_int(10000, 200000),
                "is_active": is_active,
                "enterprise_id": enterprise_id,
            }
            drivers.append(driver)
        return drivers

    @transaction.atomic
    def handle(self, *args, **options):
        import time
        enterprise_id = options['enterprise_id']
        number_of_cars = options['number_of_cars']
        number_of_drivers = number_of_cars

        fake_ru = Faker('ru_RU')
        fake_en = Faker('en_US')

        start = time.time()
        vehicles_data = self.generate_vehicles(enterprise_id, number_of_cars, fake_ru, fake_en)
        drivers_data = self.generate_drivers(enterprise_id, number_of_drivers, fake_ru)
        print("Generation took", time.time() - start)

        start = time.time()
        vehicles_created = [Vehicle.objects.create(**v) for v in vehicles_data]
        print("Vehicles insert took", time.time() - start)

        start = time.time()
        drivers_created = [Driver.objects.create(**d) for d in drivers_data]
        print("Drivers insert took", time.time() - start)

        start = time.time()
        for i, (vehicle, driver) in enumerate(zip(vehicles_created, drivers_created)):
            is_active = ((i + 1) % 10 == 0)
            VehicleDriver.objects.create(vehicle=vehicle, driver=driver, is_active=is_active)
        print("VehicleDriver generation took", time.time() - start)


        self.stdout.write(self.style.SUCCESS(
            f"Создано {len(vehicles_created)} машин и {len(drivers_created)} водителей для автопарка {enterprise_id}"
        ))
