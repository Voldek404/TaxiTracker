from django.db import transaction
from faker import Faker
import logging
import random

from TaxiTracker.vehicles.models import VehicleDriver
from .models import Vehicle, Driver

_ALLOWED_LETTERS = list("АВЕКМНОРСТУХ")
_REGION_CODES = [
    "77", "97", "99", "50", "90", "150",
    "78", "98", "23", "93", "61", "161",
    "52", "152", "66", "96", "196"
]

class CarGenerator:
    def __init__(self, enterprise_id: int, number_of_cars: int, number_of_drivers: int):
        self.enterprise_id = enterprise_id
        self.number_of_cars = number_of_cars
        self.number_of_drivers = number_of_drivers
        self.fake_ru = Faker('ru_RU')
        self.vehicles = []
        self.drivers = []

    def generate_plate(self) -> str:
        l1 = random.choice(_ALLOWED_LETTERS)
        l2 = random.choice(_ALLOWED_LETTERS)
        l3 = random.choice(_ALLOWED_LETTERS)
        digits = f"{random.randint(0, 999):03d}"
        region = random.choice(_REGION_CODES)
        return f"{l1}{digits}{l2}{l3}{region}"

    def generate_vehicles(self):
        for _ in range(self.number_of_cars):
            vehicle = {
                "prod_date": self.fake_ru.date_of_birth(),
                "odometer": self.fake_ru.random_int(30000, 200000),
                "price": self.fake_ru.random_int(30000, 200000),
                "color": self.fake_ru.color_name(),
                "plate_number": self.generate_plate(),
                "enterprise": self.enterprise_id,
            }
            self.vehicles.append(vehicle)
        return self.vehicles

    def generate_drivers(self):
        for i in range(self.number_of_drivers):
            is_active = ((i + 1) % 10 == 0)
            driver = {
                "full_name": self.fake_ru.name(),
                "salary": self.fake_ru.random_int(10000, 200000),
                "is_active": is_active,
                "enterprise": self.enterprise_id,
            }
            self.drivers.append(driver)
        return self.drivers

    def db_filler(self):
        drivers_created = []
        vehicles_created = []
        for obj in self.vehicles:
            vehicle = Vehicle.objects.create(**obj)
            vehicles_created.append(vehicle)
        for obj in self.drivers:
            driver = Driver.objects.create(**obj)
            drivers_created.append(driver)
        for vehicle, driver in zip(vehicles_created, drivers_created):
            VehicleDriver.objects.create(
                vehicle=vehicle,
                driver=driver,
                is_active=True
            )


if __name__ == "__main__":
    enterprise_id = int(input("Введите ID автопарка: "))
    number_of_cars = int(input("Введите количество машин: "))
    number_of_drivers = number_of_cars

    generator = CarGenerator(enterprise_id, number_of_cars, number_of_drivers)
    vehicles = generator.generate_vehicles()
    drivers = generator.generate_drivers()

    with transaction.atomic():
        generator.db_filler()

    print("\nСгенерированные машины:")
    for v in vehicles:
        print(v)

    print("\nСгенерированные водители:")
    for d in drivers:
        print(d)


