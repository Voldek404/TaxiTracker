from rest_framework import generics
from vehicles.models import Vehicle
from vehicles.serializers import VehicleSerializer

class VehicleApiView(generics.ListAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
