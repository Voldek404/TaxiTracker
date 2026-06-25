
import aiohttp
import asyncio
import math

API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"  # not secret at all
BASE_URL = "https://graphhopper.com/api/1"

API_KEY_2 = "9e61f84ec90f419193bae5004f179977"  # not secret at all
SECOND_URL = "https://api.geoapify.com/v1/geocode/reverse"

SEM = asyncio.Semaphore(10)


# ==============================
# FORWARD GEOCODING
# ==============================

async def fetch_json(session, url, params, retries=2):
    async with SEM:
        for attempt in range(retries + 1):
            try:
                async with session.get(url, params=params, timeout=10) as r:
                    r.raise_for_status()
                    return await r.json()
            except aiohttp.ClientError:
                if attempt == retries:
                    return None
                await asyncio.sleep(0.3 * (attempt + 1))



async def geocode_address(session, address):
    url = f"{BASE_URL}/geocode"

    params = {
        "q": address,
        "limit": 1,
        "key": API_KEY,
    }

    data = await fetch_json(session, url, params)

    if data and data.get("hits"):
        hit = data["hits"][0]
        return hit["point"]["lat"], hit["point"]["lng"]

    return None, None


# ==============================
# REVERSE GEOCODING (PRIMARY)
# ==============================

async def reverse_geocode(session, lat, lon):
    url = f"{BASE_URL}/geocode"

    params = {
        "reverse": "true",
        "point": f"{lat},{lon}",
        "key": API_KEY,
    }

    data = await fetch_json(session, url, params)

    if data and data.get("hits"):
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

    return await reverse_geocode_second(session, lat, lon)


# ==============================
# REVERSE GEOCODING (FALLBACK)
# ==============================

async def reverse_geocode_second(session, lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "apiKey": API_KEY_2,
    }

    data = await fetch_json(session, SECOND_URL, params)

    if not data:
        return None

    features = data.get("features")
    if not features:
        return None

    return features[0]["properties"].get("formatted")


# ==============================
# ROUTE BUILDING
# ==============================

async def build_route(session, start, end):
    url = f"{BASE_URL}/route"

    params = [
        ("point", f"{start[0]},{start[1]}"),
        ("point", f"{end[0]},{end[1]}"),
        ("vehicle", "car"),
        ("points_encoded", "false"),
        ("key", API_KEY),
    ]

    data = await fetch_json(session, url, params)

    if not data or not data.get("paths"):
        return []

    return data["paths"][0]["points"]["coordinates"]


async def geocode_many(session, addresses):
    tasks = [
        geocode_address(session, addr)
        for addr in addresses
    ]
    return await asyncio.gather(*tasks)

async def reverse_many(session, points):
    tasks = [
        reverse_geocode(session, lat, lon)
        for lat, lon in points
    ]
    return await asyncio.gather(*tasks)


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
            interpolated.append((
                lon1 + (lon2 - lon1) * frac,
                lat1 + (lat2 - lat1) * frac
            ))

    interpolated.append(route[-1])
    return interpolated