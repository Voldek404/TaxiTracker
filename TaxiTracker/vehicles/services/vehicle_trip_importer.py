import csv
import json

from django.utils.dateparse import parse_datetime
from django.contrib.gis.geos import Point as GEOSPoint

from vehicles.models import VehicleTrip, VehicleTrackPoint

from vehicles.services.dto import RawPointDTO, ProcessedPointDTO
from vehicles.services import geocoding
from django.db import transaction


class UnsupportedFileFormat(Exception):
    pass


class InvalidImportFile(Exception):
    pass


class VehicleTripImporter:

    def import_file(self, file, vehicle):

        rows = self._load_file(file)

        created = 0

        for row in rows:
            with transaction.atomic():

                raw_points = self._extract_points(row)
                processed_points = self._process_points(raw_points)

                if not processed_points:
                    continue

                trip = self._create_trip(vehicle, processed_points)

                self._create_track_points(vehicle, trip, processed_points)

                created += 1

        return {"created": created}

    # -------------------------
    # file parsing
    # -------------------------

    def _load_file(self, file):

        if file.name.endswith(".json"):
            return self._load_json(file)

        if file.name.endswith(".csv"):
            return self._load_csv(file)

        raise UnsupportedFileFormat()

    def _load_json(self, file):
        try:
            data = json.load(file)
        except Exception:
            raise InvalidImportFile()

        return data if isinstance(data, list) else [data]

    def _load_csv(self, file):
        try:
            decoded = file.read().decode("utf-8").splitlines()
            return list(csv.DictReader(decoded))
        except Exception:
            raise InvalidImportFile()

    # -------------------------
    # DTO mapping layer
    # -------------------------

    def _extract_points(self, row) -> list[RawPointDTO]:

        points = row.get("points") or []

        if not points and ("lat" in row or "address" in row):
            points = [row]

        dtos = []

        for p in points:
            dtos.append(
                RawPointDTO(
                    lat=p.get("lat"),
                    lng=p.get("lng"),
                    address=p.get("address"),
                    timestamp=p.get("timestamp"),
                )
            )

        return dtos

    # -------------------------
    # domain transformation
    # -------------------------

    def _process_points(
        self,
        points: list[RawPointDTO],
    ) -> list[ProcessedPointDTO]:

        processed = []

        for p in points:

            timestamp = parse_datetime(p.timestamp)
            if not timestamp:
                continue

            lat = p.lat
            lng = p.lng

            if (lat is None or lng is None) and p.address:
                lat, lng = self._geocode(p.address)

            if lat is None or lng is None:
                continue

            processed.append(
                ProcessedPointDTO(
                    lat=float(lat),
                    lng=float(lng),
                    timestamp=timestamp,
                )
            )

        processed.sort(key=lambda x: x.timestamp)

        return processed


    def _create_trip(self, vehicle, points):

        return VehicleTrip.objects.create(
            vehicle=vehicle,
            start_timestamp=points[0].timestamp,
            end_timestamp=points[-1].timestamp,
        )

    def _create_track_points(self, vehicle, trip, points):

        VehicleTrackPoint.objects.bulk_create([
            VehicleTrackPoint(
                vehicle=vehicle,
                point=GEOSPoint(p.lng, p.lat, srid=4326),
                timestamp=p.timestamp,
                trip=trip,
            )
            for p in points
        ])