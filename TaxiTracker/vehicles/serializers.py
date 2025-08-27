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
    vehicles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Driver
        fields = ['id','vehicles', 'is_active', 'enterprise']

    def get_vehicles(self, obj):
        vehicles_qs = Vehicle.objects.filter(driver=obj)
        return VehiclesSerializer(vehicles_qs, many=True).data


class EnterprisesSerializer(serializers.ModelSerializer):
    drivers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vehicles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Enterprise
        fields = ['name', 'city', 'vehicles', 'drivers']
