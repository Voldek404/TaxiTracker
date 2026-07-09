from confluent_kafka import Consumer
import json
import asyncio

from generator import generate_track



consumer = Consumer({

    "bootstrap.servers":
        "localhost:9092",

    "group.id":
        "tracking-service",

    "auto.offset.reset":
        "earliest"

})


consumer.subscribe([
    "track.generate"
])



def start():

    while True:

        msg = consumer.poll(1)


        if msg is None:
            continue


        data = json.loads(
            msg.value()
        )


        asyncio.run(
            generate_track(

                data["vehicle_id"],

                data["track_km"],

                data["interval"],

                data["step"]

            )
        )