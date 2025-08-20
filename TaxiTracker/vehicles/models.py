from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib import admin
from django.db.models.fields import IntegerField





class Brand(models.Model):
    product_name = models.CharField(max_length=100)
    car_class = models.CharField(max_length=2)
    fuel_tank_capacity = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(999)])
    maximum_load_kg = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99999)])
    country_of_origin = models.CharField(max_length=100)
    number_of_passengers = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(60)])

    def __str__(self):
        return f"Марка авто {self.product_name}"

class Vehicle(models.Model):
    prod_date = models.DateField()
    odometer = models.IntegerField(validators=[MaxValueValidator(1000000)])
    price = models.IntegerField(validators=[MaxValueValidator(10000000)])
    color = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=9, blank = True)

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null = True, related_name='vehicles')

    def __str__(self):
        return f"id = {self.id} Авто. Госномер {self.plate_number}. Модель - {self.brand}"