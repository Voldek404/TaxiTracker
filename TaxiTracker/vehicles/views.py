from django.http import JsonResponse
from django.views.i18n import JSONCatalog
from rest_framework import generics
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, ManagersSerializer
from rest_framework.response import Response


class VehiclesApiView(generics.ListAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer


class BrandsApiView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer



class DriversApiView(generics.ListAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer



class EnterprisesApiView(generics.ListAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer


class VehiclesDetailApiView(generics.RetrieveAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    lookup_field = 'id'


class DriversDetailApiView(generics.RetrieveAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    lookup_field = 'id'


class EnterprisesDetailApiView(generics.RetrieveAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    lookup_field = 'id'


class ManagersApiView(generics.ListAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer


class ManagersDetailApiView(generics.RetrieveAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    lookup_field = 'id'
