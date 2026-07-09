from django.core.management.base import BaseCommand
from confluent_kafka import Consumer
import json

from vehicles.models import VehicleTrackPoint, Vehicle
from django.contrib.gis.geos import Point



class Command(BaseCommand):

    def handle(self,*args,**kwargs):

        consumer = Consumer({

            "bootstrap.servers":
                "localhost:9092",

            "group.id":
                "django-tracking",

            "auto.offset.reset":
                "latest"
        })


        consumer.subscribe(
            ["vehicle.locations"]
        )


        while True:

            msg = consumer.poll(1)


            if msg is None:
                continue


            data = json.loads(
                msg.value()
            )


            vehicle = Vehicle.objects.get(
                id=data["vehicle_id"]
            )


            VehicleTrackPoint.objects.create(

                vehicle=vehicle,

                point=Point(
                    data["lon"],
                    data["lat"],
                    srid=4326
                ),

                timestamp=data["timestamp"]

            )