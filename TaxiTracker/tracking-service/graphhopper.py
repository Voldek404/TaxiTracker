import aiohttp


API_KEY = "9d21bd0b-f7f2-4438-9643-0ae8a5807b52"

BASE_URL = "https://graphhopper.com/api/1"


async def build_route(start, end):

    url = f"{BASE_URL}/route"

    params = [
        ("point", f"{start[0]},{start[1]}"),
        ("point", f"{end[0]},{end[1]}"),
        ("vehicle", "car"),
        ("points_encoded", "false"),
        ("key", API_KEY),
    ]


    async with aiohttp.ClientSession() as session:

        async with session.get(
            url,
            params=params
        ) as response:

            data = await response.json()


    return (
        data["paths"][0]
        ["points"]
        ["coordinates"]
    )