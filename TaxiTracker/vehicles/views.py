from multiprocessing.context import AuthenticationError

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login
from django.views.generic import FormView, ListView
from rest_framework import generics, filters
from vehicles.models import Vehicle, Brand, Driver, Enterprise, VehicleDriver, Manager
from vehicles.serializers import VehiclesSerializer, BrandsSerializer, DriversSerializer, EnterprisesSerializer, \
    ManagersSerializer
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import DjangoModelPermissions,DjangoObjectPermissions, IsAuthenticated
from rest_framework.exceptions import PermissionDenied, APIException
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework_extensions.mixins import PaginateByMaxMixin
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from urllib.parse import urlencode



class UserLoginView(FormView):
    template_name = 'authentication/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect('/dashboard/')


class UserLogoutView(LogoutView):
    next_page = '/login/'


class ManagerDashboardView(ListView):
    template_name = 'authentication/dashboard.html'
    model = Enterprise
    context_object_name = 'enterprises'

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return user.managers.enterprises.all()
        raise PermissionDenied("Вы не менеджер")



class MyPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100
    page_query_param = 'page'

    available_sizes = [10, 20, 50]

    def get_paginated_response(self, data):
        base_url = self.request.build_absolute_uri().split('?')[0]
        current_size = int(self.request.GET.get(self.page_size_query_param, self.page_size))

        return Response({
            'size_buttons': [
                {
                    'size': size,
                    'url': self.build_size_url(size),
                    'active': size == current_size,
                    'label': str(size)
                } for size in self.available_sizes
            ],

            'results': data
        })

    def build_size_url(self, size):
        params = self.request.GET.copy()
        params[self.page_size_query_param] = size
        params[self.page_query_param] = 1  # Сбрасываем на первую страницу
        return f"{self.request.build_absolute_uri().split('?')[0]}?{urlencode(params)}"

    def build_page_url(self, page_num):
        params = self.request.GET.copy()
        params[self.page_query_param] = page_num
        return f"{self.request.build_absolute_uri().split('?')[0]}?{urlencode(params)}"

    def get_page_range(self):
        current = self.page.number
        total = self.page.paginator.num_pages

        # Показываем до 5 страниц вокруг текущей
        start = max(1, current - 2)
        end = min(total, current + 2)

        return range(start, end + 1)



class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Запрещенная операция"
    default_code = "conflict"


class VehiclesApiView(generics.ListCreateAPIView):

    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    pagination_class = MyPagination


    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ['color', 'price', 'odometer']

    def handle_exception(self, exc):
        response = super().handle_exception(exc)
        if isinstance(exc, PermissionDenied):
            return Response({"ОШИБКА"}, status=status.HTTP_400_BAD_REQUEST)
        return response

    def perform_create(self, serializer):
        try:
            manager = Manager.objects.get(user=self.request.user)
            serializer.save(enterprise=manager.enterprises.first())
        except Manager.DoesNotExist:
            raise PermissionDenied("У вас нет прав на создание автомобиля")

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class VehiclesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        user = self.request.user
        pk = self.kwargs['pk']
        try:
            obj = Vehicle._base_manager.get(pk=pk)
        except Vehicle.DoesNotExist:
            raise Http404

        if hasattr(user, 'managers'):
            if not user.managers.enterprises.filter(pk=obj.enterprise_id).exists():
                raise PermissionDenied("У вас нет прав на просмотр этой машины")
        if self.request.method == "DELETE"  and not user.is_superuser:
            raise ConflictError()

        return obj


class BrandsApiView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandsSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Vehicle.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class DriversApiView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'managers'):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class EnterprisesApiView(generics.ListCreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

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
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]


class ManagersDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

