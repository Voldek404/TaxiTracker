from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models
import zoneinfo
import time
from django.utils import timezone

ENTERPRISE_TIMEZONES = [
    ("UTC", "UTC±00:00 — Coordinated Universal Time"),
    ("Europe/London", "UTC±00:00 — London"),
    ("Europe/Paris",  "UTC+01:00 — Paris"),
    ("Europe/Berlin", "UTC+01:00 — Berlin"),
    ("Europe/Moscow", "UTC+03:00 — Moscow"),
    ("Asia/Dubai",    "UTC+04:00 — Dubai"),
    ("Asia/Almaty",   "UTC+06:00 — Almaty"),
    ("Asia/Tashkent", "UTC+05:00 — Tashkent"),
    ("Asia/Shanghai", "UTC+08:00 — Shanghai"),
    ("Asia/Tokyo",    "UTC+09:00 — Tokyo"),
    ("America/New_York",    "UTC−05:00 — New York"),
    ("America/Chicago",     "UTC−06:00 — Chicago"),
    ("America/Denver",      "UTC−07:00 — Denver"),
    ("America/Los_Angeles", "UTC−08:00 — Los Angeles"),
]


class Enterprise(models.Model):
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        null=True,
        choices=ENTERPRISE_TIMEZONES,
    )

    def __str__(self):
        return f"id = {self.id} Наименование предприятия - {self.name}. Расположение - {self.city}. Часовой пояс - {self.timezone}"


class Driver(models.Model):
    full_name = models.CharField(max_length=100)
    salary = models.IntegerField(validators=[MaxValueValidator(250000)])
    is_active = models.BooleanField(default=True)
    active_vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_drivers",
    )

    enterprise = models.ForeignKey(
        Enterprise, on_delete=models.CASCADE, null=True, related_name="drivers"
    )

    def __str__(self):
        return f"id = {self.id} ФИО {self.full_name}."


class Brand(models.Model):
    product_name = models.CharField(max_length=100)
    car_class = models.CharField(max_length=2)
    fuel_tank_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(999)]
    )
    maximum_load_kg = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99999)]
    )
    country_of_origin = models.CharField(max_length=100)
    number_of_passengers = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)]
    )

    def __str__(self):
        return f"Марка авто {self.product_name}"


class VehicleDriver(models.Model):
    vehicle = models.ForeignKey(
        "Vehicle", on_delete=models.CASCADE, related_name="vehicle_drivers"
    )
    driver = models.ForeignKey(
        "Driver", on_delete=models.CASCADE, related_name="vehicle_drivers"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("vehicle", "driver")

    def save(self, *args, **kwargs):
        if self.is_active:
            VehicleDriver.objects.filter(vehicle=self.vehicle).exclude(
                driver=self.driver
            ).update(is_active=False)
            VehicleDriver.objects.filter(driver=self.driver, is_active=True).exclude(
                vehicle=self.vehicle
            ).update(is_active=False)

            if self.vehicle.driver_id != self.driver.id:
                Vehicle.objects.filter(id=self.vehicle.id).update(driver=self.driver)
            if not self.driver.is_active:
                Driver.objects.filter(id=self.driver.id).update(is_active=True)

        super().save(*args, **kwargs)


class Vehicle(models.Model):
    prod_date = models.DateField()
    odometer = models.IntegerField(validators=[MaxValueValidator(1000000)])
    price = models.IntegerField(validators=[MaxValueValidator(10000000)])
    color = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=9, blank=True)
    car_purchase_time = models.DateTimeField(null=True, blank=True)

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, null=True, related_name="vehicles"
    )
    enterprise = models.ForeignKey(
        Enterprise, on_delete=models.CASCADE, null=True, related_name="vehicles"
    )

    driver = models.ForeignKey(
        "Driver", on_delete=models.SET_NULL, null=True, blank=True
    )
    drivers = models.ManyToManyField(
        "Driver", through="VehicleDriver", related_name="vehicles"
    )

    def __str__(self):
        return (
            f"id = {self.id} Авто. Госномер {self.plate_number}. Модель - {self.brand}. Дата продажи - {self.car_purchase_time}"
        )

    @property
    def car_purchase_time_utc(self):
        if not self.car_purchase_time:
            return None

        if timezone.is_naive(self.car_purchase_time):
            return timezone.make_aware(self.car_purchase_time, timezone.utc)
        return self.car_purchase_time

    def save(self, *args, **kwargs):
        old_driver = None
        if self.id:
            old_vehicle = Vehicle.objects.get(id=self.id)
            old_driver = old_vehicle.driver
        super().save(*args, **kwargs)

        if self.driver != old_driver:
            self._update_driver_status()

    def _update_driver_status(self):
        if self.driver:
            self.driver.is_active = True
            self.driver.save()

            Vehicle.objects.filter(driver=self.driver).exclude(id=self.id).update(
                driver=None
            )

        if self.driver:
            other_drivers = self.drivers.exclude(id=self.driver.id)
        else:
            other_drivers = self.drivers.all()

        other_drivers.update(is_active=False)

        if self.driver:
            VehicleDriver.objects.filter(vehicle=self).exclude(
                driver=self.driver
            ).update(is_active=False)
            VehicleDriver.objects.filter(vehicle=self, driver=self.driver).update(
                is_active=True
            )
        else:
            VehicleDriver.objects.filter(vehicle=self).update(is_active=False)


class VehicleTrackPoint(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
    )
    point = models.PointField(geography=True, srid=4326)
    timestamp = models.DateTimeField(db_index=True)

    class Meta:
        indexes = (
            models.Index(fields=["vehicle", "timestamp"]),
        )

    def get_point(self, obj):
        return {"lat": obj.point.y, "lng": obj.point.x}


class VehicleTrip(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
    )
    start_timestamp = models.DateTimeField(db_index=True)
    end_timestamp = models.DateTimeField(db_index=True)
    class Meta:
        indexes = (
            models.Index(fields=["vehicle", "start_timestamp", "end_timestamp"]),
        )


class Manager(models.Model):
    full_name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    enterprises = models.ManyToManyField(
        Enterprise, related_name="managers", blank=True
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="managers"
    )

    def __str__(self):
        return f"id = {self.id} ФИО - {self.full_name}. "
