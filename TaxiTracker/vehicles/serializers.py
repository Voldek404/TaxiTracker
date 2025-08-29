from rest_framework import serializers
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['product_name', 'car_class', 'fuel_tank_capacity', 'maximum_load_kg', 'country_of_origin',
                  'number_of_passengers']


class VehiclesSerializer(serializers.ModelSerializer):
    drivers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'prod_date', 'odometer', 'price', 'color', 'brand', 'drivers']


class DriversSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    active_vehicle = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ['id', 'full_name', 'salary', 'vehicles', 'active_vehicle']

    def get_vehicles(self, obj):
        vehicles_qs = Vehicle.objects.filter(vehicle_drivers__driver=obj)
        if vehicles_qs.exists():
            return list(vehicles_qs.values_list('id', flat=True))
        return None

    def get_active_vehicle(self, obj):
        active_vds = obj.vehicle_drivers.filter(is_active=True)
        return [
            vd.vehicle.id for vd in active_vds
        ] or None


class EnterprisesSerializer(serializers.ModelSerializer):
    drivers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vehicles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Enterprise
        fields = ['name', 'city', 'vehicles', 'drivers']
