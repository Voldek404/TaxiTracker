from rest_framework import serializers
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields =['product_name','car_class','fuel_tank_capacity','maximum_load_kg','country_of_origin', 'number_of_passengers']


class VehiclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['prod_date', 'odometer', 'price', 'color', 'plate_number', 'brand']



class DriversSerializer(serializers.ModelSerializer):
    vehicles = VehiclesSerializer(many=True, read_only=True)

    class Meta:
        model = Driver
        fields = ['full_name', 'salary', 'is_active', 'vehicles', 'enterprise']

    def get_vehicles(self, obj):
        # Все машины, где этот водитель основной
        vehicles_qs = Vehicle.objects.filter(driver=obj)
        return VehiclesSerializer(vehicles_qs, many=True).data


class EnterprisesSerializer(serializers.ModelSerializer):
    vehicles = VehiclesSerializer(many=True, read_only=True)
    drivers = serializers.SerializerMethodField()

    class Meta:
        model = Enterprise
        fields = ['name', 'city', 'vehicles', 'drivers']

    def get_drivers(self, obj):
        drivers_qs = obj.drivers.all()
        return DriversSerializer(drivers_qs, many=True).data
