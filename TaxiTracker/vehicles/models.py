from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.fields import IntegerField


class Vehicle(models.Model):
    prod_date = models.DateField()
    odometer = models.IntegerField(validators=[MaxValueValidator(1000000)])
    price = models.IntegerField(validators=[MaxValueValidator(1000000)])
    country_of_origin = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    plate_number = models.CharField(max_length=9, null = True, blank = True)

    def __str__(self):
        return f"id = {self.id} Авто"