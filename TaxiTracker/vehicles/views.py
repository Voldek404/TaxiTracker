
from rest_framework import generics
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, ManagersSerializer
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated





class VehiclesApiView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        return Vehicle.objects.none()


class BrandsApiView(generics.ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer



class DriversApiView(generics.ListAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Driver.objects.all()
        if hasattr(user, 'managers'):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        return Driver.objects.none()


class EnterprisesApiView(generics.ListAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Enterprise.objects.all()
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        return Enterprise.objects.none()


class VehiclesDetailApiView(generics.RetrieveAPIView):
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


class DriversDetailApiView(generics.RetrieveAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    lookup_field = 'id'




class EnterprisesDetailApiView(generics.RetrieveAPIView):
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


class ManagersApiView(generics.ListAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer


class ManagersDetailApiView(generics.RetrieveAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    lookup_field = 'id'



