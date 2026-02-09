import time
import random
import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point as GEOSPoint
from django.utils import timezone
import math
from shapely.geometry import Point, Polygon

from vehicles.models import Vehicle, VehicleTrackPoint

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"
BASE_URL = "https://graphhopper.com/api/1"
moscow_polygon = Polygon([
    (37.6, 55.75),
    (37.6, 55.76),
    (37.62, 55.76),
    (37.62, 55.75)
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
        interval = opts["interval"]
        target_distance = opts["track_km"] * 1000  # метры

        current_lat, current_lon = 55.7558, 37.6173
        traveled = 0
        point_counter = 0

        self.stdout.write(self.style.SUCCESS(
            f"Старт трекинга авто {vehicle.id} ({vehicle.plate_number})"
        ))

        while traveled < target_distance:
            angle = random.uniform(0, 2 * 3.1415)
            distance = random.uniform(800, 3000)  # метры
            dlat = (distance / 111_320) * math.cos(angle)
            dlon = (distance / 111_320) * math.sin(angle)
            dest_lat = current_lat + dlat
            dest_lon = current_lon + dlon
            pt = Point(dest_lon, dest_lat)
            if not moscow_polygon.contains(pt):
                continue

            try:
                route = self.graphhopper_route(start=(current_lat, current_lon),
                                               end=(dest_lat, dest_lon))
            except Exception as e:
                self.stderr.write(f"Ошибка маршрута: {e}")
                continue

            for lon, lat in self.interpolate_route(route, opts["step"]):
                VehicleTrackPoint.objects.create(
                    vehicle=vehicle,
                    point=GEOSPoint(lon, lat, srid=4326),
                    timestamp=timezone.now(),
                )
                point_counter += 1

            current_lat, current_lon = dest_lat, dest_lon
            traveled += distance
            time.sleep(interval)

        self.stdout.write(self.style.SUCCESS(
            f"Генерация трека завершена. Создано точек: {point_counter}, "
            f"Пройдено: {traveled / 1000:.2f} км"
        ))
