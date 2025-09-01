
from rest_framework import generics
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, ManagersSerializer
from rest_framework.response import Response



class VehiclesApiView(generics.ListAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__manager=user.manager)
        return Vehicle.objects.none()


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

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'manager'):
            return Vehicle.objects.filter(enterprise__manager=user.manager)
        return Vehicle.objects.none()


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



