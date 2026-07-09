from confluent_kafka import Producer
import json


producer = Producer({
    "bootstrap.servers": "localhost:9092"
})


def send_location(data):

    producer.produce(
        "vehicle.locations",
        json.dumps(data).encode()
    )

    producer.flush()