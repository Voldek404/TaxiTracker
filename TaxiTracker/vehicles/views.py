from django.http import JsonResponse
from django.views.i18n import JSONCatalog
from rest_framework import generics
from vehicles.models import Vehicle, Brand
from vehicles.serializers import VehiclesSerializer, BrandsSerializer


class VehiclesApiView(generics.ListAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer



class BrandsApiView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer

class VehiclesDetailApiView(generics.RetrieveAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    lookup_field = 'id'