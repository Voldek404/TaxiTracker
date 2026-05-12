import csv
import json
from io import StringIO

from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404

from vehicles.models import (
    Vehicle,
    VehicleTrip,
)

from core.utils import make_guid


class VehicleTripsExporter:

    def export_json(
        self,
        vehicle_id,
        start=None,
        end=None,
    ):
        vehicle, trips = self._collect_data(
            vehicle_id=vehicle_id,
            start=start,
            end=end,
        )

        payload = {
            "vehicle": {
                "id": make_guid(
                    "Vehicle",
                    vehicle.id,
                ),
                "plate_number": vehicle.plate_number,
            },
            "trips": [
                self._serialize_trip(
                    trip=trip,
                    vehicle=vehicle,
                )
                for trip in trips
            ],
        }

        content = json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
            cls=DjangoJSONEncoder,
        )

        return (
            content,
            "application/json; charset=utf-8",
        )

    def export_csv(
        self,
        vehicle_id,
        start=None,
        end=None,
    ):
        vehicle, trips = self._collect_data(
            vehicle_id=vehicle_id,
            start=start,
            end=end,
        )

        output = StringIO()

        writer = csv.writer(
            output,
            lineterminator="\n",
        )

        writer.writerow([
            "trip_guid",
            "start_timestamp",
            "end_timestamp",
            "vehicle_guid",
            "vehicle_plate",
        ])

        for trip in trips:
            writer.writerow([
                make_guid(
                    "Trip",
                    trip.id,
                ),
                (
                    trip.start_timestamp.isoformat()
                    if trip.start_timestamp else ""
                ),
                (
                    trip.end_timestamp.isoformat()
                    if trip.end_timestamp else ""
                ),
                make_guid(
                    "Vehicle",
                    vehicle.id,
                ),
                vehicle.plate_number,
            ])

        return (
            output.getvalue(),
            "text/csv; charset=utf-8",
        )

    def _collect_data(
        self,
        vehicle_id,
        start=None,
        end=None,
    ):
        vehicle = get_object_or_404(
            Vehicle,
            id=vehicle_id,
        )

        trips = (
            VehicleTrip.objects
            .filter(vehicle=vehicle)
            .order_by("start_timestamp")
        )

        if start:
            trips = trips.filter(
                start_timestamp__gte=start,
            )

        if end:
            trips = trips.filter(
                end_timestamp__lte=end,
            )

        return vehicle, trips

    def _serialize_trip(
        self,
        trip,
        vehicle,
    ):
        return {
            "id": make_guid(
                "Trip",
                trip.id,
            ),
            "start_timestamp": (
                trip.start_timestamp.isoformat()
                if trip.start_timestamp else None
            ),
            "end_timestamp": (
                trip.end_timestamp.isoformat()
                if trip.end_timestamp else None
            ),
            "vehicle_id": make_guid(
                "Vehicle",
                vehicle.id,
            ),
            "vehicle_plate": vehicle.plate_number,
        }