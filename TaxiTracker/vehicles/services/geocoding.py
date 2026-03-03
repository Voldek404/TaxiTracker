import requests
import math

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"  # not secret at all
BASE_URL = "https://graphhopper.com/api/1"

API_KEY_2 = "9e61f84ec90f419193bae5004f179977"  # not secret at all
SECOND_URL = "https://api.geoapify.com/v1/geocode/reverse"


# ==============================
# FORWARD GEOCODING
# ==============================

def geocode_address(address):
    """
    Преобразует адрес в (lat, lon)
    """
    try:
        url = f"{BASE_URL}/geocode"
        params = {
            "q": address,
            "limit": 1,
            "key": API_KEY,
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("hits"):
            hit = data["hits"][0]
            return hit["point"]["lat"], hit["point"]["lng"]

    except requests.RequestException:
        return None, None

    return None, None


# ==============================
# REVERSE GEOCODING (PRIMARY)
# ==============================

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

    except requests.RequestException:
        return reverse_geocode_second(lat, lon)

    if data.get("hits"):
        hit = data["hits"][0]
        parts = []

        if hit.get("name"):
            parts.append(hit["name"])

        street = hit.get("street")
        number = hit.get("housenumber")

        if street:
            parts.append(f"{street}, {number}" if number else street)

        if not parts and hit.get("city"):
            parts.append(hit["city"])

        if hit.get("postalcode"):
            parts.append(hit["postalcode"])

        return ", ".join(parts)

    return None


# ==============================
# REVERSE GEOCODING (FALLBACK)
# ==============================

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


# ==============================
# ROUTE BUILDING
# ==============================

def build_route(start, end):
    """
    start: (lat, lon)
    end:   (lat, lon)

    Возвращает список [(lon, lat), ...]
    """

    try:
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

        if not data.get("paths"):
            return []

        return data["paths"][0]["points"]["coordinates"]

    except requests.RequestException:
        return []


# ==============================
# ROUTE INTERPOLATION
# ==============================

def interpolate_route(route, step_meters=20):


    if not route or len(route) < 2:
        return route

    interpolated = []

    for i in range(len(route) - 1):
        lon1, lat1 = route[i]
        lon2, lat2 = route[i + 1]

        dx = (lon2 - lon1) * 111_320
        dy = (lat2 - lat1) * 111_320
        segment_length = math.sqrt(dx ** 2 + dy ** 2)

        num_points = max(int(segment_length / step_meters), 1)

        for j in range(num_points):
            frac = j / num_points
            lon = lon1 + (lon2 - lon1) * frac
            lat = lat1 + (lat2 - lat1) * frac
            interpolated.append((lon, lat))

    interpolated.append(route[-1])
    return interpolated