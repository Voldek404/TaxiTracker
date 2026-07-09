from datetime import datetime, timezone
import asyncio

from producer import send_location


async def generate(vehicle_id):

    points = [
        (55.751244, 37.618423),
        (55.752244, 37.619423),
        (55.753244, 37.620423),
    ]


    for lat, lon in points:

        send_location({

            "vehicle_id": vehicle_id,

            "lat": lat,

            "lon": lon,

            "timestamp": datetime.now(timezone.utc).isoformat()
        })


        await asyncio.sleep(1)