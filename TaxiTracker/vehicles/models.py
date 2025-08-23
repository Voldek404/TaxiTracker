from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib import admin
from django.db.models.fields import IntegerField



class Enterprise(models.Model):
    name = models.CharField(max_length=50)
    city = models.CharField(max_length=50)


    def __str__(self):
        return f"id = {self.id} Наименование предприятия - {self.name}. Расположение - {self.city}"


class Driver(models.Model):
    full_name = models.CharField(max_length=100)
    salary = models.IntegerField(validators=[MaxValueValidator(250000)])

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

class Vehicle(models.Model):
    prod_date = models.DateField()
    odometer = models.IntegerField(validators=[MaxValueValidator(1000000)])
    price = models.IntegerField(validators=[MaxValueValidator(10000000)])
    color = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=9, blank = True)

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null = True, related_name='vehicles')
    enterprise = models.ForeignKey(Enterprise, on_delete=models.CASCADE, null=True, related_name='vehicles')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null = True, related_name='vehicles')


    def __str__(self):
        return f"id = {self.id} Авто. Госномер {self.plate_number}. Модель - {self.brand}"




"""
установить ключи один к одному для машины по отношению к предприятию
в админке машинки после выбора предприятия сузить выбор водителей только до тех, кто находится в данном предприятии
добавить признак активности для конкретного водителя ( новый филд?)

"""




