
from rest_framework import generics
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, ManagersSerializer
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated





class VehiclesApiView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        return Vehicle.objects.none()


class BrandsApiView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer



class DriversApiView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Driver.objects.all()
        if hasattr(user, 'managers'):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        return Driver.objects.none()


class EnterprisesApiView(generics.ListCreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Enterprise.objects.all()
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        return Enterprise.objects.none()


class VehiclesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        return Vehicle.objects.none()


class DriversDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    lookup_field = 'id'




class EnterprisesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Enterprise.objects.all()
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        return Enterprise.objects.none()


class ManagersApiView(generics.ListCreateAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer


class ManagersDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    lookup_field = 'id'



