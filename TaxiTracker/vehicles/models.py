from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib import admin
from django.db.models.fields import IntegerField
from django.contrib.auth.models import User



class Enterprise(models.Model):
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)



    def __str__(self):
        return f"id = {self.id} Наименование предприятия - {self.name}. Расположение - {self.city}"


class Driver(models.Model):
    full_name = models.CharField(max_length=100)
    salary = models.IntegerField(validators=[MaxValueValidator(250000)])
    is_active = models.BooleanField(default=True)
    active_vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_drivers"
    )

    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, related_name='drivers')

    def __str__(self):
        return f"id = {self.id} ФИО {self.full_name}."


class Brand(models.Model):
    product_name = models.CharField(max_length=100)
    car_class = models.CharField(max_length=2)
    fuel_tank_capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(999)])
    maximum_load_kg = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99999)])
    country_of_origin = models.CharField(max_length=100)
    number_of_passengers = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(60)])

    def __str__(self):
        return f"Марка авто {self.product_name}"

class VehicleDriver(models.Model):
    vehicle = models.ForeignKey("Vehicle", on_delete=models.CASCADE, related_name='vehicle_drivers')
    driver = models.ForeignKey("Driver", on_delete=models.CASCADE, related_name='vehicle_drivers')

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('vehicle', 'driver')

    def save(self, *args, **kwargs):
        if self.is_active:
            VehicleDriver.objects.filter(vehicle=self.vehicle).exclude(driver=self.driver).update(is_active=False)
            VehicleDriver.objects.filter(driver=self.driver, is_active=True).exclude(vehicle=self.vehicle).update(
                is_active=False)

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
    plate_number = models.CharField(max_length=9, blank = True)

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null = True, related_name='vehicles')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, related_name='vehicles')

    driver = models.ForeignKey("Driver", on_delete=models.SET_NULL, null=True, blank=True)
    drivers = models.ManyToManyField("Driver", through="VehicleDriver", related_name="vehicles")



    def __str__(self):
        return f"id = {self.id} Авто. Госномер {self.plate_number}. Модель - {self.brand}"

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

            Vehicle.objects.filter(driver=self.driver).exclude(id=self.id).update(driver=None)

        if self.driver:
            other_drivers = self.drivers.exclude(id=self.driver.id)
        else:
            other_drivers = self.drivers.all()

        other_drivers.update(is_active=False)

        if self.driver:
            VehicleDriver.objects.filter(vehicle=self).exclude(driver=self.driver).update(is_active=False)
            VehicleDriver.objects.filter(vehicle=self, driver=self.driver).update(is_active=True)
        else:
            VehicleDriver.objects.filter(vehicle=self).update(is_active=False)


class Manager(models.Model):
    full_name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    enterprises = models.ManyToManyField(
        Enterprise,
        related_name='managers',
        blank=True
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='managers')

    def __str__(self):
        return f"id = {self.id} ФИО - {self.full_name}. "