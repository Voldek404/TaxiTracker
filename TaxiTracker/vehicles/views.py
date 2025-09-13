
from rest_framework import generics
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, ManagersSerializer
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.authentication import BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404





class VehiclesApiView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(enterprise=user.managers.enterprises.first())

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")




class BrandsApiView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")




class DriversApiView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class EnterprisesApiView(generics.ListCreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'managers'):
            serializer.save(manager=user.managers)
            return
        raise PermissionDenied("У вас нет прав на создание предприятия")

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        raise PermissionDenied("У вас нет прав на просмотр")


class VehiclesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        obj = get_object_or_404(Vehicle, pk=self.kwargs['pk'])
        if hasattr(user, 'managers'):
            if not user.managers.enterprises.filter(pk=obj.enterprise_id).exists():
                raise PermissionDenied("У вас нет прав на просмотр этой машины")
        else:
            raise PermissionDenied("У вас нет прав на просмотр")
        return obj


class DriversDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")



class EnterprisesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        raise PermissionDenied("У вас нет прав на просмотр")


class ManagersApiView(generics.ListCreateAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class ManagersDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]



