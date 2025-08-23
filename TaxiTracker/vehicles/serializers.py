from rest_framework import serializers
from vehicles.models import Vehicle, Brand, Driver, Enterprise


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields =['product_name','car_class','fuel_tank_capacity','maximum_load_kg','country_of_origin', 'number_of_passengers']


class VehiclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields =['prod_date','odometer','price','color','plate_number', 'brand']


class DriversSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields =['full_name','salary','enterprise']


class EnterprisesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields =['name','city']
