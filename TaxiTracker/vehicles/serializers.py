from rest_framework import serializers
from vehicles.models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    Manager,
    VehicleTrackPoint,
    VehicleTrip,
)
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from django.utils import timezone
from zoneinfo import ZoneInfo
import json


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "product_name",
            "car_class",
            "fuel_tank_capacity",
            "maximum_load_kg",
            "country_of_origin",
            "number_of_passengers",
        ]


class VehiclesSerializer(serializers.ModelSerializer):
    car_purchase_time = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "plate_number",
            "prod_date",
            "odometer",
            "price",
            "color",
            "brand",
            "car_purchase_time",
        ]

    def get_car_purchase_time(self, obj):
        if not obj.car_purchase_time:
            return None

        utc_time = obj.car_purchase_time_utc
        if timezone.is_naive(utc_time):
            utc_time = timezone.make_aware(utc_time, timezone.utc)

        tz_name = obj.enterprise.timezone or "UTC"
        local_time = utc_time.astimezone(ZoneInfo(tz_name))
        return local_time.isoformat()


class DriversSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    active_vehicle = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ["id", "full_name", "salary", "vehicles", "active_vehicle"]

    def get_vehicles(self, obj):
        vehicles_qs = Vehicle.objects.filter(vehicle_drivers__driver=obj)
        if vehicles_qs.exists():
            return list(vehicles_qs.values_list("id", flat=True))
        return []

    def get_active_vehicle(self, obj):
        active_vds = (
            obj.vehicle_drivers.filter(is_active=True)
            .values_list("vehicle__id", flat=True)
            .first()
        )
        if active_vds:
            return active_vds
        return -1


class EnterprisesSerializer(serializers.ModelSerializer):
    drivers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    vehicles = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Enterprise
        fields = ["name", "city", "vehicles", "drivers"]


class ManagersSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    drivers = serializers.SerializerMethodField()

    class Meta:
        model = Manager
        fields = ["full_name", "enterprises", "vehicles", "drivers"]

    def get_drivers(self, obj):
        drivers = Driver.objects.filter(
            enterprise__in=obj.enterprises.all()
        ).values_list("id", flat=True)
        return list(drivers)

    def get_vehicles(self, obj):
        vehicles = Vehicle.objects.filter(
            enterprise__in=obj.enterprises.all()
        ).select_related("enterprise")

        vehicles_list = []

        for v in vehicles:
            car_purchase_time = None
            if v.car_purchase_time:
                utc_time = v.car_purchase_time
                if timezone.is_naive(utc_time):
                    utc_time = timezone.make_aware(utc_time, timezone.utc)

                tz_name = v.enterprise.timezone or "UTC"
                local_time = utc_time.astimezone(ZoneInfo(tz_name))
                car_purchase_time = local_time.isoformat()

            vehicles_list.append(
                {
                    "id": v.id,
                    "plate_number": v.plate_number,
                    "brand": v.brand.id if v.brand else None,
                    "car_purchase_time": car_purchase_time,
                    "enterprise": v.enterprise.id if v.enterprise else None,
                }
            )

        return vehicles_list


class VehicleTrackPointSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()

    class Meta:
        model = VehicleTrackPoint
        fields = ["trip", "point", "timestamp"]

    def get_timestamp(self, obj):
        utc_time = obj.timestamp
        tz_name = (
            obj.vehicle.enterprise.timezone
            if hasattr(obj.vehicle, "enterprise")
            else "UTC"
        )
        local_time = utc_time.astimezone(ZoneInfo(tz_name))
        return local_time.isoformat()


class VehicleTrackPointGeoSerializer(serializers.Serializer):

    def to_representation(self, instance):
        tz_name = "UTC"
        if (
            hasattr(instance.vehicle, "enterprise")
            and instance.vehicle.enterprise.timezone
        ):
            tz_name = instance.vehicle.enterprise.timezone

        timestamp_formatted = instance.timestamp.astimezone(
            ZoneInfo(tz_name)
        ).isoformat()

        feature_data = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(instance.point.x), float(instance.point.y)],
            },
            "properties": {
                "timestamp": timestamp_formatted,
                "trip_id": instance.trip_id,
            },
        }

        return json.loads(json.dumps(feature_data, ensure_ascii=False))
