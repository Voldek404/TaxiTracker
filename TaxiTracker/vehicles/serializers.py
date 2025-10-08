from rest_framework import serializers
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['product_name', 'car_class', 'fuel_tank_capacity', 'maximum_load_kg', 'country_of_origin',
                  'number_of_passengers']


class VehiclesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'prod_date', 'odometer', 'price', 'color', 'brand']



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
        return []

    def get_active_vehicle(self, obj):
        active_vds = obj.vehicle_drivers.filter(is_active=True).values_list('vehicle__id', flat=True).first()
        if active_vds:
            return active_vds
        return -1


class EnterprisesSerializer(serializers.ModelSerializer):
    drivers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vehicles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Enterprise
        fields = ['name', 'city', 'vehicles', 'drivers']


class ManagersSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    drivers = serializers.SerializerMethodField()

    class Meta:
        model = Manager
        fields = ['full_name', 'enterprises', 'vehicles', 'drivers']

    def get_drivers(self, obj):
        drivers = Driver.objects.filter(
            enterprise__in=obj.enterprises.all()
        ).values_list('id', flat=True)
        return list(drivers)

    def get_vehicles(self, obj):
        vehicles = Vehicle.objects.filter(
            enterprise__in=obj.enterprises.all()
        ).values_list('id', flat=True)
        return list(vehicles)
