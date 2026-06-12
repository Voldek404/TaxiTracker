import time
import random
import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point as GEOSPoint
from django.utils import timezone
import math
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
from django.utils.dateparse import parse_datetime

from vehicles.models import Vehicle, VehicleTrackPoint, VehicleTrip

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"
BASE_URL = "https://graphhopper.com/api/1"
moscow_polygon = Polygon([
    (37.35, 55.55),
    (37.35, 55.95),
    (37.85, 55.95),
    (37.85, 55.55),
])


class Command(BaseCommand):

    help = "Генерация реалистичного GPS-трека по улицам через GraphHopper /route"

    def graphhopper_route(self, start, end):
        url = f"{BASE_URL}/route"
        params = [
            ("point", f"{start[0]},{start[1]}"),
            ("point", f"{end[0]},{end[1]}"),
            ("vehicle", "car"),
            ("points_encoded", "false"),
            ("key", API_KEY),
        ]

        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if "paths" not in data or not data["paths"]:
            raise Exception("Нет маршрута в ответе GraphHopper")

        return data["paths"][0]["points"]["coordinates"]  # [(lon, lat)]

    def add_arguments(self, parser):
        parser.add_argument("--vehicle-id", type=int, required=True)
        parser.add_argument("--interval", type=int, default=10, help="секунды между точками")
        parser.add_argument("--track-km", type=float, default=5, help="суммарная длина трека в км")
        parser.add_argument("--step", type=float, default=20, help="шаг между точками в метрах")
        parser.add_argument("--trip-id", type=int, required=False)
        parser.add_argument("--start-datetime", type=str, required=False)

    def interpolate_route(self, route, step):
        interpolated = []
        for i in range(len(route) - 1):
            lon1, lat1 = route[i]
            lon2, lat2 = route[i + 1]

            dx = (lon2 - lon1) * 111_320  
            dy = (lat2 - lat1) * 111_320
            segment_length = math.sqrt(dx ** 2 + dy ** 2)

            num_points = max(int(segment_length / step), 1)

            for j in range(num_points):
                frac = j / num_points
                lon = lon1 + (lon2 - lon1) * frac
                lat = lat1 + (lat2 - lat1) * frac
                interpolated.append((lon, lat))
        interpolated.append(route[-1])
        return interpolated

    def handle(self, *args, **opts):
        vehicle = Vehicle.objects.get(id=opts["vehicle_id"])
        trip_id = opts.get("trip_id")

        if trip_id:
            trip = VehicleTrip.objects.get(id=trip_id, vehicle=vehicle)
        else:
            now = timezone.now()
            trip = VehicleTrip.objects.create(
                vehicle=vehicle,
                start_timestamp=now,
                end_timestamp=now + timezone.timedelta(minutes=10),
            )

        interval = opts["interval"]
        target_distance = opts["track_km"] * 1000

        min_lon, min_lat, max_lon, max_lat = moscow_polygon.bounds
        current_lon = random.uniform(min_lon, max_lon)
        current_lat = random.uniform(min_lat, max_lat)

        traveled = 0
        point_counter = 0

        self.stdout.write(self.style.SUCCESS(
            f"Старт трекинга авто {vehicle.id} ({vehicle.plate_number})"
        ))

        # Генерация конечной точки
        angle = random.uniform(0, 2 * math.pi)
        dlat = (target_distance / 111_320) * math.cos(angle)
        dlon = (target_distance / (111_320 * math.cos(math.radians(current_lat)))) * math.sin(angle)

        dest_lat = current_lat + dlat
        dest_lon = current_lon + dlon

        # Маршрут
        route = self.graphhopper_route(
            start=(current_lat, current_lon),
            end=(dest_lat, dest_lon)
        )

        interpolated = self.interpolate_route(route, step=opts["step"])
        total_points = len(interpolated)

        self.stdout.write(self.style.SUCCESS(f"Всего точек: {total_points}"))

        # points_to_create = []
        prev = None
        traveled = 0
        point_counter = 0
        if opts.get("start_datetime"):
            base_time = parse_datetime(opts["start_datetime"])
        else:
            base_time = timezone.now()
        interval = opts["interval"]

        for i, (lon, lat) in enumerate(interpolated):
            try:
                print("TRY CREATE", lon, lat)

                obj = VehicleTrackPoint.objects.create(
                    vehicle=vehicle,
                    point=GEOSPoint(lon, lat, srid=4326),
                    timestamp=base_time + timezone.timedelta(seconds=i * interval),
                )

                print("CREATED ID:", obj.id)

            except Exception as e:
                print("ERROR:", e)
                break

            if prev:
                traveled += geodesic((prev[1], prev[0]), (lat, lon)).km

            # point = VehicleTrackPoint(
            #     vehicle=vehicle,
            #     point=GEOSPoint(lon, lat, srid=4326),
            #     timestamp=base_time + timezone.timedelta(seconds=i * interval),
            # )
            # points_to_create.append(point)

            prev = (lon, lat)
            point_counter += 1

            time.sleep(0.1)

            # прогресс каждые 100 точек
            if i % 100 == 0:
                self.stdout.write(f"{i}/{total_points}")

        # массовая вставка в базу (быстро)
        # VehicleTrackPoint.objects.bulk_create(points_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Генерация трека завершена.\n"
            f"Создано точек: {point_counter}\n"
            f"Пройдено: {traveled:.2f} км"
        ))
