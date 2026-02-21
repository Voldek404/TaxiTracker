import requests
from django.conf import settings

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"
BASE_URL = "https://graphhopper.com/api/1"


def reverse_geocode(lat, lon):
    url = f"{BASE_URL}/geocode"
    params = {
        "reverse": "true",
        "point": f"{lat},{lon}",
        "key": API_KEY,
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    if "hits" in data and len(data["hits"]) > 0:
        hit = data["hits"][0]
        parts = []

        # Берём сначала имя объекта
        if hit.get("name"):
            parts.append(hit["name"])

        # Потом улицу и номер дома, если есть
        street = hit.get("street")
        number = hit.get("housenumber")
        if street:
            if number:
                parts.append(f"{street}, {number}")
            else:
                parts.append(street)

        # Добавляем город, если нет ничего выше
        if not parts and hit.get("city"):
            parts.append(hit["city"])

        # Можно добавить почтовый индекс
        if hit.get("postalcode"):
            parts.append(hit["postalcode"])

        # Склеиваем через запятую
        address = ", ".join(parts)
        return address

    return None
