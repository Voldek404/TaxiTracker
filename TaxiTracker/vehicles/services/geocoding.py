import requests
from django.conf import settings

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"
BASE_URL = "https://graphhopper.com/api/1"
API_KEY_2= '9e61f84ec90f419193bae5004f179977'
SECOND_URL = "https://api.geoapify.com/v1/geocode/reverse"


def reverse_geocode(lat, lon):
    try:
        url = f"{BASE_URL}/geocode"
        params = {
            "reverse": "true",
            "point": f"{lat},{lon}",
            "key": API_KEY,
        }
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        return reverse_geocode_second(lat, lon)

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
        if hit.get("postalcode"):
            parts.append(hit["postalcode"])
        address = ", ".join(parts)
        return address

    return None

def reverse_geocode_second(lat, lon):
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "apiKey": API_KEY_2,
        }

        r = requests.get(SECOND_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        features = data.get("features")
        if not features:
            return None

        return features[0]["properties"].get("formatted")

    except requests.RequestException:
        return None
