from confluent_kafka import Producer
import json


producer = Producer({
    "bootstrap.servers": "localhost:9092"
})


def send_track_generation(
        vehicle_id,
        track_km=5,
        interval=10,
        step=20
):

    producer.produce(
        "track.generate",
        json.dumps({
            "vehicle_id": vehicle_id,
            "track_km": track_km,
            "interval": interval,
            "step": step
        }).encode()
    )

    producer.flush()