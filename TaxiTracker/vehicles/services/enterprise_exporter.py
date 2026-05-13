import csv
import json
from io import StringIO

from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404

from vehicles.models import (
    Enterprise,
    Vehicle,
)

from vehicles.export_utils import make_guid


class EnterpriseExporter:

    def export_json(self, enterprise_id):
        enterprise, vehicles = self._collect_data(enterprise_id)

        drivers_map = {}
        brands_map = {}
        vehicles_data = []
        trips_data = []

        for vehicle in vehicles:
            vehicle_data = self._serialize_vehicle(
                vehicle=vehicle,
                enterprise=enterprise,
                drivers_map=drivers_map,
                brands_map=brands_map,
                trips_data=trips_data,
            )

            vehicles_data.append(vehicle_data)

        payload = {
            "enterprise": {
                "id": make_guid("Enterprise", enterprise.id),
                "name": enterprise.name,
                "city": enterprise.city,
                "timezone": enterprise.timezone,
            },
            "brands": list(brands_map.values()),
            "drivers": list(drivers_map.values()),
            "vehicles": vehicles_data,
            "vehicle_trips": trips_data,
        }

        content = json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
            cls=DjangoJSONEncoder,
        )

        return content, "application/json; charset=utf-8"

    def export_csv(self, enterprise_id):
        enterprise, vehicles = self._collect_data(enterprise_id)

        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")

        writer.writerow([
            "vehicle_guid",
            "production_date",
            "purchase_date",
            "odometer",
            "price",
            "color",
            "plate_number",
            "brand_guid",
            "enterprise_guid",
            "driver_guids",
        ])

        for vehicle in vehicles:
            writer.writerow([
                make_guid("Vehicle", vehicle.id),
                vehicle.prod_date.isoformat() if vehicle.prod_date else "",
                vehicle.car_purchase_time.isoformat()
                if vehicle.car_purchase_time else "",
                vehicle.odometer,
                vehicle.price,
                vehicle.color,
                vehicle.plate_number,
                make_guid("Brand", vehicle.brand.id)
                if vehicle.brand else "",
                make_guid("Enterprise", enterprise.id),
                ", ".join([
                    str(make_guid("Driver", driver.id))
                    for driver in vehicle.drivers.all()
                ]),
            ])

        return output.getvalue(), "text/csv; charset=utf-8-sig"

    def _collect_data(self, enterprise_id):
        enterprise = get_object_or_404(
            Enterprise,
            id=enterprise_id,
        )

        vehicles = (
            Vehicle.objects
            .filter(enterprise=enterprise)
            .select_related("brand")
            .prefetch_related(
                "drivers",
                "vehicletrip_set",
            )
        )

        return enterprise, vehicles

    def _serialize_vehicle(
        self,
        vehicle,
        enterprise,
        drivers_map,
        brands_map,
        trips_data,
    ):
        vehicle_guid = make_guid("Vehicle", vehicle.id)

        # Brand
        if vehicle.brand:
            brand_guid = make_guid(
                "Brand",
                vehicle.brand.id,
            )

            brands_map[brand_guid] = {
                "id": brand_guid,
                "product_name": vehicle.brand.product_name,
                "car_class": vehicle.brand.car_class,
                "fuel_tank_capacity": vehicle.brand.fuel_tank_capacity,
                "maximum_load_kg": vehicle.brand.maximum_load_kg,
                "country_of_origin": vehicle.brand.country_of_origin,
                "number_of_passengers": (
                    vehicle.brand.number_of_passengers
                ),
            }
        else:
            brand_guid = None

        # Drivers
        driver_guids = []

        for driver in vehicle.drivers.all():
            driver_guid = make_guid(
                "Driver",
                driver.id,
            )

            drivers_map[driver_guid] = {
                "id": driver_guid,
                "full_name": driver.full_name,
                "salary": driver.salary,
                "is_active": driver.is_active,
            }

            driver_guids.append(driver_guid)

        # Trips
        for trip in vehicle.vehicletrip_set.all():
            trips_data.append({
                "id": make_guid(
                    "VehicleTrip",
                    trip.id,
                ),
                "vehicle_id": vehicle_guid,
                "start_timestamp": (
                    trip.start_timestamp.isoformat()
                    if trip.start_timestamp else None
                ),
                "end_timestamp": (
                    trip.end_timestamp.isoformat()
                    if trip.end_timestamp else None
                ),
            })

        return {
            "id": vehicle_guid,
            "production_date": (
                vehicle.prod_date.isoformat()
                if vehicle.prod_date else None
            ),
            "purchase_date": (
                vehicle.car_purchase_time.isoformat()
                if vehicle.car_purchase_time else None
            ),
            "odometer": vehicle.odometer,
            "price": vehicle.price,
            "color": vehicle.color,
            "plate_number": vehicle.plate_number,
            "brand_id": brand_guid,
            "enterprise_id": make_guid(
                "Enterprise",
                enterprise.id,
            ),
            "drivers": driver_guids,
        }