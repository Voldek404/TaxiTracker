from time import perf_counter
from asgiref.sync import sync_to_async
from django.db.models import Max
from django.http import JsonResponse

from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse
from asgiref.sync import sync_to_async
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from django.views.generic import TemplateView
from geopy.distance import geodesic
from django.db.models import Max
from django.db import connection, reset_queries
import time
import gpxpy
import csv
from django.core.cache import cache
from vehicles.export_utils import make_guid
from django.db.models import OuterRef, Subquery
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
    View,
)
from django.urls import reverse_lazy
from rest_framework import generics, filters
from vehicles.models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    Manager,
    VehicleTrackPoint,
    VehicleTrip,
    ENTERPRISE_TIMEZONES,
    ResultPair,
    WeeklyReport,
    DailyReport,
    RandomReport,
    MonthlyReport,
)
from vehicles.serializers import (
    VehiclesSerializer,
    BrandsSerializer,
    DriversSerializer,
    EnterprisesSerializer,
    ManagersSerializer,
    VehicleTrackPointSerializer,
    VehicleTrackPointGeoSerializer,
    ResultPairSerializer,
    VehicleReportSerializer,
    DailyReportSerializer,
    WeeklyReportSerializer,
    MonthlyReportSerializer,
    RandomReportSerializer,
)
from vehicles.forms import VehicleForm
from django.utils.dateparse import parse_datetime
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (
    DjangoModelPermissions,
    DjangoObjectPermissions,
    IsAuthenticated,
)
import datetime

from django.views import View
from django.template import loader
from rest_framework.exceptions import PermissionDenied, APIException
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework_extensions.mixins import PaginateByMaxMixin
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from urllib.parse import urlencode
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.renderers import JSONRenderer
from django.http import HttpResponse
from datetime import datetime, timedelta
from vehicles.permissions import IsManager,HasEnterpriseAccess, HasTripAccess, CanDeleteVehicle


from vehicles.serializers import VehicleTripSerializer
from vehicles.services.geocoding import (
    geocode_address,
    build_route,
    interpolate_route,
)
from vehicles.services.enterprise_exporter import (
    EnterpriseExporter,
)
from vehicles.services.vehicle_trips_exporter import (
    VehicleTripsExporter,
)
from vehicles.services.delete_vehicles import (
    delete_vehicles,
)
from vehicles.services.enterprise_importer import (
    EnterpriseImporter,
    InvalidImportFile,
    UnsupportedFileFormat,
)
from vehicles.services.vehicle_importer import (
    InvalidImportFile,
    UnsupportedFileFormat,
    VehicleImporter,
)
from vehicles.selectors.vehicle import (
    get_manager_vehicles,
)
from vehicles.selectors.brand import get_user_brands
from vehicles.selectors.enterprise import (
    get_user_enterprises,
)


from django.contrib.gis.geos import Point as GEOSPoint

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from notifications.service import send_telegram_notification
from telegram_bot.models import TelegramProfile


class MyPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100
    page_query_param = "page"

    available_sizes = [10, 20, 50]

    def get_paginated_response(self, data):
        current_size = int(
            self.request.GET.get(self.page_size_query_param, self.page_size)
        )

        return Response(
            {
                "size_buttons": [
                    {
                        "size": size,
                        "url": self.build_size_url(size),
                        "active": size == current_size,
                        "label": str(size),
                    }
                    for size in self.available_sizes
                ],
                "results": data,
            }
        )

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
        start = max(1, current - 2)
        end = min(total, current + 2)

        return range(start, end + 1)


class UserLoginView(FormView):
    template_name = "authentication/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect("/dashboard/")


class UserLogoutView(LogoutView):
    next_page = "/login/"


class ManagerDashboardView(ListView):
    template_name = "authentication/dashboard.html"
    model = Enterprise
    context_object_name = "enterprises"

    def get_queryset(self):
        return get_user_enterprises(
            self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["timezone_choices"] = Enterprise._meta.get_field("timezone").choices
        return context


class EnterpriseTimezoneUpdateView(View):

    def post(self, request, pk):
        data = json.loads(request.body)
        enterprise = get_object_or_404(Enterprise, pk=pk)
        enterprise.timezone = data["timezone"]
        enterprise.save()
        return JsonResponse({"status": "ok"})


class SetTimezoneView(View):
    def post(self, request):
        data = json.loads(request.body)
        tzname = data.get("timezone")
        if tzname:
            request.session["django_timezone"] = tzname
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error"}, status=400)


class ManagerVehicleDashboardView(ListView):
    template_name = "authentication/vehicles_dashboard.html"
    model = Vehicle
    paginate_by = 100
    context_object_name = "vehicles"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enterprise_id"] = self.kwargs.get("pk")
        return context

    def get_queryset(self):
        user = self.request.user

        if not hasattr(user, "managers"):
            raise PermissionDenied("У вас нет прав на просмотр")

        enterprise_id = self.kwargs.get("pk")

        if not user.managers.enterprises.filter(id=enterprise_id).exists():
            raise PermissionDenied("Нет доступа к этому предприятию")

        return Vehicle.objects.filter(enterprise_id=enterprise_id).select_related(
            "brand",
            "enterprise",
            "driver"
        )



class ManagerVehicleCreateView(CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "authentication/vehicle_create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_invalid(self, form):
        print("FORM INVALID")
        print(form.errors)

        return super().form_invalid(form)

    def form_valid(self, form):
        manager = self.request.user.managers

        form.instance.enterprise = manager.enterprises.first()

        # Сначала сохраняем автомобиль
        response = super().form_valid(form)

        # После сохранения отправляем уведомление
        try:
            from telegram_bot.models import TelegramProfile

            profile = TelegramProfile.objects.get(manager=manager)

            send_telegram_notification(
                telegram_id=profile.telegram_id,
                message=(
                    f"🚗 Автомобиль успешно создан\n\n"
                    f"Марка: {self.object.brand}\n"
                    f"Госномер: {self.object.plate_number}\n"
                    f"Цвет: {self.object.color}\n"
                    f"Дата выпуска: {self.object.prod_date}"
                )
            )

            print(
                f"Telegram notification sent: {profile.telegram_id}"
            )

        except TelegramProfile.DoesNotExist:
            print(
                f"У менеджера {manager.id} нет Telegram профиля"
            )

        except Exception as e:
            print(
                f"Ошибка отправки Telegram: {e}"
            )

        return response


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enterprise_id"] = self.request.user.managers.enterprises.first().id
        context["button_text"] = "Создать автомобиль"
        return context

    def get_success_url(self):
        enterprise_id = self.request.user.managers.enterprises.first().id
        return reverse_lazy("vehicles", kwargs={"pk": enterprise_id})


class ManagerVehicleUpdateView(UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = "authentication/vehicle_details.html"
    context_object_name = "ui_vehicle_details"
    paginate_by = 50

    def get_object(self):
        vehicle = super().get_object()
        manager = self.request.user.managers

        if not manager.enterprises.filter(pk=vehicle.enterprise_id).exists():
            raise PermissionDenied

        return vehicle

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        manager = self.request.user.managers
        vehicle = self.object

        context["manager_enterprises"] = manager.enterprises.all()

        enterprises = manager.enterprises.all()
        drivers = Driver.objects.filter(enterprise__in=enterprises).select_related(
            "enterprise"
        )

        context["available_drivers"] = drivers
        start = self.request.GET.get("start")
        end = self.request.GET.get("end")

        start_dt = parse_datetime(start) if start else None
        end_dt = parse_datetime(end) if end else None
        trips = VehicleTrip.objects.filter(vehicle=vehicle)

        if start_dt:
            trips = trips.filter(start_timestamp__gte=start_dt)

        if end_dt:
            trips = trips.filter(end_timestamp__lte=end_dt)

        trips = trips.order_by("-start_timestamp")

        paginator = Paginator(trips, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["trips"] = page_obj

        context["filter_start"] = start
        context["filter_end"] = end

        return context

    def get_success_url(self):
        return reverse("ui_vehicle_details", kwargs={"pk": self.object.pk})



class VehiclesBulkDeleteView(View):

    def post(self, request, *args, **kwargs):

        vehicle_ids = request.POST.getlist("vehicle_ids")

        try:
            deleted_count = delete_vehicles(vehicle_ids)

            messages.success(request, f"{deleted_count} автомобилей удалено.")

        except Exception as e:
            messages.warning(request, str(e))

        return redirect(request.META.get("HTTP_REFERER", "/"))


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
    ordering_fields = ["color", "price", "odometer"]

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

        manager = getattr(
            self.request.user,
            "managers",
            None,
        )

        if not manager:
            raise PermissionDenied(
                "У вас нет прав на просмотр",
            )

        return get_manager_vehicles(
            manager,
        )


class VehiclesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.select_related("enterprise", "brand")
    serializer_class = VehiclesSerializer
    permission_classes = [IsAuthenticated, IsManager, CanDeleteVehicle]
    authentication_classes = [JWTAuthentication]

    def get_cache_key(self, pk):
        return f"vehicle:resp:{pk}"

    def retrieve(self, request, *args, **kwargs):
        key = f"vehicle:resp:{kwargs['pk']}"

        cached = cache.get(key)
        if cached is not None:

            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)

        cache.set(key, response.data, 300)
        return response



class BrandsApiView(generics.ListCreateAPIView):

    serializer_class = BrandsSerializer
    permission_classes = [DjangoModelPermissions, IsManager]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

    def get_queryset(self):
        user = self.request.user
        manager = getattr(user, "managers", None)
        return get_user_brands(user)

    def list(self, request, *args, **kwargs):
        key = f"brands:raw:{request.user.id}"

        cached = cache.get(key)
        if cached:
            return Response(cached)

        qs = get_user_brands(request.user)
        data = BrandsSerializer(qs, many=True).data

        cache.set(key, data, 300)
        return Response(data)


class DriversApiView(generics.ListCreateAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "managers"):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class EnterprisesApiView(generics.ListCreateAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    permission_classes = [DjangoModelPermissions, HasEnterpriseAccess,]
    authentication_classes = [JWTAuthentication]
    pagination_class = MyPagination

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, "managers"):
            serializer.save(manager=user.managers)
            return
        raise PermissionDenied("У вас нет прав на создание предприятия")

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "managers"):
            return user.managers.enterprises.all()
        raise PermissionDenied("У вас нет прав на просмотр")


class DriversDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Driver.objects.all()
    serializer_class = DriversSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "managers"):
            return Driver.objects.filter(enterprise__in=user.managers.enterprises.all())
        raise PermissionDenied("У вас нет прав на просмотр")


class EnterprisesDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Enterprise.objects.all()
    serializer_class = EnterprisesSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):

        return get_user_enterprises(
            self.request.user,
        )


class ManagersApiView(generics.ListCreateAPIView):
    queryset = Manager.objects.prefetch_related(
        "enterprises",
        "enterprises__drivers",
        "enterprises__vehicles__brand",
        "enterprises__vehicles__enterprise",
    )
    serializer_class = ManagersSerializer
    permission_classes = [DjangoModelPermissions]
    authentication_classes = [JWTAuthentication]


class ManagersDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Manager.objects.all()
    serializer_class = ManagersSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class VehicleTrackAPIView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]

    def get_cache_key(self, request):
        user = request.user

        vehicle_id = request.query_params.get("vehicle_id")
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        output_type = request.query_params.get("type")

        return f"track:{user.id}:{vehicle_id}:{start}:{end}:{output_type}"

    def get_queryset(self):
        user = self.request.user

        manager = user.managers
        qs = VehicleTrackPoint.objects.filter(
            vehicle__enterprise__in=manager.enterprises.all()
        )
        vehicle_id = self.request.query_params.get("vehicle_id")
        if vehicle_id:
            qs = qs.filter(vehicle_id=vehicle_id)

        start = self.request.query_params.get("start")
        if start:
            start_dt = parse_datetime(start)
            if start_dt:
                qs = qs.filter(timestamp__gte=start_dt)

        end = self.request.query_params.get("end")
        if end:
            end_dt = parse_datetime(end)
            if end_dt:
                qs = qs.filter(timestamp__lte=end_dt)

        return qs.order_by("timestamp")

    def get_serializer_class(self):
        if self.request.query_params.get("type") == "geojson":
            return VehicleTrackPointGeoSerializer
        if self.request.query_params.get("type") == "json":
            return VehicleTrackPointSerializer

    def list(self, request, *args, **kwargs):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached:
            return HttpResponse(
                json.dumps(cached, ensure_ascii=False),
                content_type="application/json; charset=utf-8",
            )
        queryset = self.get_queryset()

        if self.request.query_params.get("type") == "geojson":
            serializer = VehicleTrackPointGeoSerializer(queryset, many=True)
            data = {"type": "FeatureCollection", "features": serializer.data}
            return HttpResponse(
                json.dumps(data, ensure_ascii=False, indent=2),
                content_type="application/json; charset=utf-8",
            )
        else:
            serializer = VehicleTrackPointSerializer(queryset, many=True)
            data = {
                "count": queryset.count(),
                "next": None,
                "previous": None,
                "results": serializer.data,
            }

        cache.set(cache_key, data, timeout=180)

        return HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8",
        )


class VehicleTripPointsRangeAPIView(generics.ListAPIView):
    serializer_class = VehicleTrackPointGeoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):
        cache_key = f"trip_points_range:{self.kwargs.get('pk')}:{self.request.query_params.get('start')}:{self.request.query_params.get('end')}:{self.request.user.id}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        user = self.request.user

        manager = user.managers
        vehicle_id = self.kwargs.get("pk")
        if not vehicle_id:
            raise PermissionDenied("Не указан vehicle_id")

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        start_dt = parse_datetime(start) if start else None
        end_dt = parse_datetime(end) if end else None

        trips = VehicleTrip.objects.filter(
            vehicle_id=vehicle_id,
            vehicle__enterprise__in=manager.enterprises.all(),
        )
        if start_dt:
            trips = trips.filter(start_timestamp__gte=start_dt)
        if end_dt:
            trips = trips.filter(end_timestamp__lte=end_dt)

        qs = (
            VehicleTrackPoint.objects.filter(vehicle_id=vehicle_id)
            .annotate(
                trip_id=Subquery(
                    trips.filter(
                        start_timestamp__lte=OuterRef("timestamp"),
                        end_timestamp__gte=OuterRef("timestamp"),
                    ).values("id")[:1]
                )
            )
            .filter(trip_id__isnull=False)
        )

        if start_dt:
            qs = qs.filter(timestamp__gte=start_dt)
        if end_dt:
            qs = qs.filter(timestamp__lte=end_dt)

        cache.set(cache_key, qs, 300)

        return qs.order_by("timestamp")


class VehicleTripsAPIView(generics.ListAPIView):
    serializer_class = VehicleTripSerializer
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated, IsManager]

    def get_queryset(self):

        user = self.request.user

        manager = user.managers
        vehicle_id = self.kwargs.get("pk")

        if not vehicle_id:
            raise PermissionDenied("Не указан vehicle_id")

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        cache_key = f"trips_qs:{user.id}:{vehicle_id}:{start}:{end}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        start_dt = parse_datetime(start) if start else None
        end_dt = parse_datetime(end) if end else None

        trips = VehicleTrip.objects.filter(
            vehicle_id=vehicle_id,
            vehicle__enterprise__in=manager.enterprises.all(),
        )
        if start_dt:
            trips = trips.filter(start_timestamp__gte=start_dt)

        if end_dt:
            trips = trips.filter(end_timestamp__lte=end_dt)

        start_point_subquery = (
            VehicleTrackPoint.objects.filter(
                vehicle=OuterRef("vehicle"),
                timestamp__gte=OuterRef("start_timestamp"),
                timestamp__lte=OuterRef("end_timestamp"),
            )
            .order_by("timestamp")
            .values("id")[:1]
        )

        end_point_subquery = (
            VehicleTrackPoint.objects.filter(
                vehicle=OuterRef("vehicle"),
                timestamp__gte=OuterRef("start_timestamp"),
                timestamp__lte=OuterRef("end_timestamp"),
            )
            .order_by("-timestamp")
            .values("id")[:1]
        )

        qs = trips.annotate(
            start_point_id=Subquery(start_point_subquery),
            end_point_id=Subquery(end_point_subquery),
        ).order_by("-start_timestamp")

        cache.set(cache_key, qs, 300)
        return qs


class VehicleTripPointsView(LoginRequiredMixin, View):

    def get_cache_key(self, user_id, vehicle_id, trip_id):
        return f"trip_points:{user_id}:{vehicle_id}:{trip_id}"

    def get(self, request, vehicle_id):
        trip_id = request.GET.get("trip_id")
        user = request.user
        if not hasattr(user, "managers"):
            return JsonResponse({"detail": "Нет доступа"}, status=403)

        cache_key = self.get_cache_key(user.id, vehicle_id, trip_id)
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse({"points": cached})

        manager = user.managers

        try:
            trip = VehicleTrip.objects.get(
                id=trip_id,
                vehicle_id=vehicle_id,
                vehicle__enterprise__in=manager.enterprises.all(),
            )
        except VehicleTrip.DoesNotExist:
            return JsonResponse({"points": []})  # поездка не найдена / нет доступа

        qs = VehicleTrackPoint.objects.filter(
            vehicle_id=vehicle_id,
            timestamp__gte=trip.start_timestamp,
            timestamp__lte=trip.end_timestamp,
        ).order_by("timestamp")

        data = [
            {"lat": p.point.y, "lng": p.point.x, "timestamp": p.timestamp.isoformat()}
            for p in qs
        ]

        cache.set(cache_key, data, timeout=300)
        print("CACHE KEY:", cache_key)
        print("CACHE GET:", cache.get(cache_key))
        return JsonResponse({"points": data})


class EnterpriseExportView(View):

    exporter = EnterpriseExporter()

    def get_cache_key(self, enterprise_id, format_type):
        return f"enterprise_export:{enterprise_id}:{format_type}"

    def get(self, request, enterprise_id):
        format_type = request.GET.get(
            "format",
            "csv",
        )
        cache_key = self.get_cache_key(enterprise_id, format_type)

        cached = cache.get(cache_key)
        if cached:
            content, content_type, ext = cached

            response = HttpResponse(
                content=content,
                content_type=content_type,
            )

            response["Content-Disposition"] = (
                f'attachment; filename="enterprise_{enterprise_id}.{ext}"'
            )
            return response

        if format_type == "json":
            content, content_type = self.exporter.export_json(enterprise_id)
            ext = "json"

        else:
            content, content_type = self.exporter.export_csv(enterprise_id)
            ext = "csv"

        cache.set(cache_key, (content, content_type, ext), timeout=600)

        response = HttpResponse(
            content=content,
            content_type=content_type,
        )

        response["Content-Disposition"] = (
            f"attachment; " f'filename="enterprise_{enterprise_id}.{ext}"'
        )

        return response


class VehicleTripsExportView(View):

    exporter = VehicleTripsExporter()

    def get(self, request, vehicle_id):

        if not hasattr(request.user, "managers"):
            return JsonResponse(
                {"detail": "Нет доступа"},
                status=403,
            )

        format_type = request.GET.get("format", "csv")
        start = request.GET.get("start")
        end = request.GET.get("end")

        if format_type == "json":
            content, content_type = self.exporter.export_json(
                vehicle_id=vehicle_id,
                start=start,
                end=end,
            )
            ext = "json"

        else:
            content, content_type = self.exporter.export_csv(
                vehicle_id=vehicle_id,
                start=start,
                end=end,
            )
            ext = "csv"

        response = HttpResponse(
            content=content,
            content_type=content_type,
        )

        response["Content-Disposition"] = (
            f"attachment; " f'filename="vehicle_{vehicle_id}_trips.{ext}"'
        )

        return response


class EnterpriseImportView(LoginRequiredMixin, View):

    importer = EnterpriseImporter()

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Файл не выбран")
            return redirect("enterprise_details")

        try:
            imported_count = self.importer.import_file(
                file=file,
                manager=getattr(request.user, "managers", None),
            )

        except UnsupportedFileFormat:
            messages.error(
                request,
                "Неподдерживаемый формат файла",
            )

        except InvalidImportFile:
            messages.error(
                request,
                "Файл поврежден или имеет неверный формат",
            )

        else:
            if imported_count:
                messages.success(
                    request,
                    f"Импортировано {imported_count} предприятий",
                )
            else:
                messages.warning(
                    request,
                    "Не удалось импортировать ни одного предприятия",
                )

        return redirect("enterprise_details")


class VehicleImportView(View):

    importer = VehicleImporter()

    def post(
        self,
        request,
        pk,
    ):
        file = request.FILES.get("file")

        if not file:

            messages.error(
                request,
                "Выберите файл для импорта",
            )

            return redirect(
                "vehicles",
                pk=pk,
            )

        try:

            result = self.importer.import_file(
                file=file,
                enterprise_id=pk,
            )

        except UnsupportedFileFormat:

            messages.error(
                request,
                ("Неподдерживаемый формат " "файла. " "Используйте CSV или JSON"),
            )

        except InvalidImportFile:

            messages.error(
                request,
                "Неверный или поврежденный файл",
            )

        else:

            for warning in result["warnings"]:
                messages.warning(
                    request,
                    warning,
                )

            if result["count"]:

                messages.success(
                    request,
                    (f"Импортировано " f"{result['count']} " f"автомобилей"),
                )

            else:

                messages.warning(
                    request,
                    ("Не удалось импортировать " "ни одного автомобиля"),
                )

        return redirect(
            "vehicles",
            pk=pk,
        )


class VehicleTripImportView(View):

    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Файл не выбран")
            return redirect("ui_vehicle_details", pk=vehicle.id)

        try:
            if file.name.endswith(".json"):
                rows = json.load(file)
            elif file.name.endswith(".csv"):
                decoded = file.read().decode("utf-8").splitlines()
                rows = list(csv.DictReader(decoded))
            else:
                messages.error(request, "Неподдерживаемый формат")
                return redirect("ui_vehicle_details", pk=vehicle.id)

            created = 0

            for row in rows:
                points_data = row.get("points") or []

                if not points_data and ("lat" in row or "address" in row):
                    points_data = [row]

                processed_points = []

                for p in points_data:
                    timestamp = parse_datetime(p.get("timestamp"))
                    if not timestamp:
                        continue

                    lat = p.get("lat")
                    lng = p.get("lng")

                    if (lat is None or lng is None) and p.get("address"):
                        lat, lng = geocode_address(p["address"])
                        if lat is None or lng is None:
                            continue

                    if lat is None or lng is None:
                        continue

                    processed_points.append(
                        {"lat": float(lat), "lng": float(lng), "timestamp": timestamp}
                    )

                if not processed_points:
                    messages.warning(request, "Пропущена поездка без точек")
                    continue

                processed_points.sort(key=lambda x: x["timestamp"])

                trip = VehicleTrip.objects.create(
                    vehicle=vehicle,
                    start_timestamp=processed_points[0]["timestamp"],
                    end_timestamp=processed_points[-1]["timestamp"],
                )

                track_points = [
                    VehicleTrackPoint(
                        vehicle=vehicle,
                        point=GEOSPoint(p["lng"], p["lat"], srid=4326),
                        timestamp=p["timestamp"],
                    )
                    for p in processed_points
                ]
                VehicleTrackPoint.objects.bulk_create(track_points)

                created += 1

            messages.success(request, f"Импортировано поездок: {created}")

        except Exception as e:
            messages.error(request, f"Ошибка импорта: {str(e)}")

        return redirect("ui_vehicle_details", pk=vehicle.id)


class ReportPageView(TemplateView):
    template_name = "report_page.html"


class BaseReportAPIView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_filtered_points(self, request):
        user = request.user
        if not hasattr(user, "managers"):
            return Response({"detail": "Нет доступа"}, status=403)
        manager = user.managers

        vehicle_ids = request.GET.getlist("vehicle_ids")
        if not vehicle_ids:
            return Response({"detail": "Не выбраны автомобили"}, status=400)

        start = parse_date(request.GET.get("start"))
        end = parse_date(request.GET.get("end"))

        qs = VehicleTrackPoint.objects.filter(
            vehicle_id__in=vehicle_ids,
            vehicle__enterprise__in=manager.enterprises.all(),
        )

        if start and end:
            start_dt = datetime.combine(start, datetime.min.time())
            end_dt = datetime.combine(end, datetime.max.time())
            qs = qs.filter(timestamp__range=(start_dt, end_dt))
        elif start:
            start_dt = datetime.combine(start, datetime.min.time())
            qs = qs.filter(timestamp__gte=start_dt)
        elif end:
            end_dt = datetime.combine(end, datetime.max.time())
            qs = qs.filter(timestamp__lte=end_dt)

        return qs.order_by("vehicle_id", "timestamp")

    def calculate_distance(self, points):
        distance = 0.0
        prev_point = None

        for p in points:
            current_coords = (p.point.y, p.point.x)  # (lat, lon)
            if prev_point:
                prev_coords = (prev_point.point.y, prev_point.point.x)
                distance += geodesic(prev_coords, current_coords).km
            prev_point = p

        return round(distance, 2)

    def group_by_day(self, points):
        daily_points = {}
        for p in points:
            day = p.timestamp.date()
            daily_points.setdefault(day, []).append(p)
        return daily_points

    def get_report_type(self):
        if isinstance(self, DailyReportAPIView):
            return "daily"
        elif isinstance(self, WeeklyReportAPIView):
            return "weekly"
        elif isinstance(self, MonthlyReportAPIView):
            return "monthly"
        elif isinstance(self, RandomReportAPIView):
            return "random"
        return "unknown"


class DailyReportAPIView(BaseReportAPIView):

    def get_cache_key(self, request):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"daily_report:{user.id}:{vehicle_ids}:{start}:{end}"

    def get(self, request):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        report_type = self.get_report_type()
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicle_ids = request.GET.getlist("vehicle_ids")

        for vid in vehicle_ids:
            try:
                vehicle = Vehicle.objects.get(id=vid)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle_id=vid)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": report_type,
                    }
                )
                continue

            daily_points = self.group_by_day(vehicle_points)
            for day, pts in daily_points.items():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": str(day),
                        "value": round(self.calculate_distance(pts), 2),
                        "report_type": report_type,
                    }
                )

        cache.set(cache_key, results, timeout=300)

        return Response(results)


class WeeklyReportAPIView(BaseReportAPIView):

    def get_cache_key(self, request):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"daily_report:{user.id}:{vehicle_ids}:{start}:{end}"

    def get(self, request):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        report_type = self.get_report_type()
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicle_ids = request.GET.getlist("vehicle_ids")

        for vid in vehicle_ids:
            try:
                vehicle = Vehicle.objects.get(id=vid)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle_id=vid)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": report_type,
                    }
                )
                continue

            daily_points = self.group_by_day(vehicle_points)
            weekly = {}
            for day, pts in daily_points.items():
                week_start = day - timedelta(days=day.weekday())
                weekly.setdefault(week_start, []).extend(pts)

            for week_start, pts in weekly.items():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": f"{week_start} - {week_start + timedelta(days=6)}",
                        "value": round(self.calculate_distance(pts), 2),
                        "report_type": report_type,
                    }
                )
        cache.set(cache_key, results, timeout=300)

        return Response(results)


class MonthlyReportAPIView(BaseReportAPIView):

    def get_cache_key(self, request):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"daily_report:{user.id}:{vehicle_ids}:{start}:{end}"

    def get(self, request):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        report_type = self.get_report_type()
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicle_ids = request.GET.getlist("vehicle_ids")

        for vid in vehicle_ids:
            try:
                vehicle = Vehicle.objects.get(id=vid)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle_id=vid)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": report_type,
                    }
                )
                continue

            monthly = {}
            for p in vehicle_points:
                month_key = p.timestamp.strftime("%Y-%m")
                monthly.setdefault(month_key, []).append(p)

            for month, pts in monthly.items():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": month,
                        "value": round(self.calculate_distance(pts), 2),
                        "report_type": report_type,
                    }
                )
        cache.set(cache_key, results, timeout=300)
        return Response(results)


class RandomReportAPIView(BaseReportAPIView):

    def get_cache_key(self, request, metric):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"random_report:{metric}:{user.id}:{vehicle_ids}:{start}:{end}"

    def get(self, request):
        metric = request.GET.get("metric")

        cache_key = self.get_cache_key(request, metric)

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicles = set(points.values_list("vehicle_id", flat=True))

        for vid in vehicles:
            try:
                vehicle = Vehicle.objects.get(id=vid)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle_id=vid)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": metric,
                    }
                )
                continue

            if metric == "average_per_day":
                daily_points = self.group_by_day(vehicle_points)
                total_distance = sum(
                    self.calculate_distance(pts) for pts in daily_points.values()
                )
                days = len(daily_points)
                avg = total_distance / days if days else 0
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": f"{days} дня/дней",
                        "value": round(avg, 2),
                        "report_type": "Средний пробег в день",
                    }
                )

            elif metric == "max_day":
                daily_points = self.group_by_day(vehicle_points)
                max_dist = 0
                max_day = None
                for day, pts in daily_points.items():
                    dist = self.calculate_distance(pts)
                    if dist > max_dist:
                        max_dist = dist
                        max_day = day
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": str(max_day),
                        "value": round(max_dist, 2),
                        "report_type": "День с максимальным пробегом",
                    }
                )

            elif metric == "total_distance":
                dist = self.calculate_distance(vehicle_points)
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": f"{vehicle_points.first().timestamp.date() if vehicle_points.exists() else ''} - {vehicle_points.last().timestamp.date() if vehicle_points.exists() else ''}",
                        "value": round(dist, 2),
                        "report_type": "Общий пробег",
                    }
                )
        cache.set(cache_key, results, timeout=300)
        return Response(results)


class BaseReportTelegramAPIView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]


    def get_filtered_points(self, request):
        user = request.user
        if not hasattr(user, "managers"):
            return Response({"detail": "Нет доступа"}, status=403)
        manager = user.managers

        vehicle_pns = request.GET.getlist("vehicle_pns")
        if not vehicle_pns:
            return Response({"detail": "Не выбраны автомобили"}, status=400)

        start = parse_date(request.GET.get("start"))
        end = parse_date(request.GET.get("end"))

        qs = VehicleTrackPoint.objects.filter(
            vehicle__plate_number__in=vehicle_pns,
            vehicle__enterprise__in=manager.enterprises.all(),
        )

        if start and end:
            start_dt = datetime.combine(start, datetime.min.time())
            end_dt = datetime.combine(end, datetime.max.time())
            qs = qs.filter(timestamp__range=(start_dt, end_dt))
        elif start:
            start_dt = datetime.combine(start, datetime.min.time())
            qs = qs.filter(timestamp__gte=start_dt)
        elif end:
            end_dt = datetime.combine(end, datetime.max.time())
            qs = qs.filter(timestamp__lte=end_dt)

        return qs.order_by("vehicle__plate_number", "timestamp")

    def calculate_distance(self, points):
        distance = 0.0
        prev_point = None

        for p in points:
            current_coords = (p.point.y, p.point.x)  # (lat, lon)
            if prev_point:
                prev_coords = (prev_point.point.y, prev_point.point.x)
                distance += geodesic(prev_coords, current_coords).km
            prev_point = p

        return round(distance, 2)

    def group_by_day(self, points):
        daily_points = {}
        for p in points:
            day = p.timestamp.date()
            daily_points.setdefault(day, []).append(p)
        return daily_points

    def get_report_type(self):
        if isinstance(self, DailyReportTelegramAPIView):
            return "daily"
        elif isinstance(self, MonthlyReportTelegramAPIView):
            return "monthly"
        # elif isinstance(self, MonthlyTelegramReportAPIView):
        #     return "monthly"
        # elif isinstance(self, RandomReportAPIView):
        #     return "random"
        return "unknown"


class DailyReportTelegramAPIView(BaseReportTelegramAPIView):

    def get_cache_key(self, request):
        user = request.user

        vehicle_pns = ",".join(sorted(request.GET.getlist("vehicle_pns")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"daily_telegram:{user.id}:{vehicle_pns}:{start}:{end}"

    def get(self, request):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        report_type = self.get_report_type()
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicle_pns = request.GET.getlist("vehicle_pns")

        for pns in vehicle_pns:
            try:
                vehicle = Vehicle.objects.get(plate_number=pns)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle__plate_number=pns)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": report_type,
                    }
                )
                continue

            daily_points = self.group_by_day(vehicle_points)
            for day, pts in daily_points.items():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": str(day),
                        "value": round(self.calculate_distance(pts), 0),
                        "report_type": report_type,
                    }
                )

        cache.set(cache_key, results, timeout=300)

        return Response(results)


class MonthlyReportTelegramAPIView(BaseReportTelegramAPIView):

    def get_cache_key(self, request):
        user = request.user

        vehicle_pns = ",".join(sorted(request.GET.getlist("vehicle_pns")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"daily_telegram:{user.id}:{vehicle_pns}:{start}:{end}"

    def get(self, request):
        cache_key = self.get_cache_key(request)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        report_type = self.get_report_type()
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        results = []
        vehicle_pns = request.GET.getlist("vehicle_pns")

        for pns in vehicle_pns:
            try:
                vehicle = Vehicle.objects.get(plate_number=pns)
            except Vehicle.DoesNotExist:
                continue

            vehicle_points = points.filter(vehicle__plate_number=pns)
            if not vehicle_points.exists():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": "-",
                        "value": 0,
                        "report_type": report_type,
                    }
                )
                continue

            monthly = {}
            for p in vehicle_points:
                month_key = p.timestamp.strftime("%Y-%m")
                monthly.setdefault(month_key, []).append(p)

            for month, pts in monthly.items():
                results.append(
                    {
                        "vehicle": vehicle.plate_number,
                        "duration": month,
                        "value": round(self.calculate_distance(pts), 0),
                        "report_type": report_type,
                    }
                )

        cache.set(cache_key, results, timeout=300)
        return Response(results)


class BaseFleetReportAPIView(APIView):
    """
    Базовый класс для отчетов по автопарку.
    Подклассы указывают report_type = 'daily' или 'monthly'.
    """

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    report_type = "unknown"  # daily или monthly

    def get_filtered_points(self, request):
        """Фильтрует VehicleTrackPoint по автопарку и диапазону дат"""
        user = request.user
        if not hasattr(user, "managers"):
            return Response({"detail": "Нет доступа"}, status=403)

        manager = user.managers
        enterprise_id = request.GET.get("enterprise_id")
        if not enterprise_id:
            return Response({"detail": "Не указан автопарк"}, status=400)

        vehicles = Vehicle.objects.filter(enterprise_id=enterprise_id)
        if not vehicles.exists():
            return Response({"detail": "В автопарке нет машин"}, status=400)

        start = request.GET.get("start")
        end = request.GET.get("end")
        if not start or not end:
            return Response({"detail": "Нужны start и end даты"}, status=400)

        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)

        qs = VehicleTrackPoint.objects.filter(
            vehicle__in=vehicles, timestamp__gte=start_dt, timestamp__lt=end_dt
        ).order_by("vehicle__plate_number", "timestamp")

        return qs

    def calculate_distance(self, points):
        """Считает суммарный пробег по списку точек"""
        distance = 0.0
        prev_point = None
        for p in points:
            if not p.point:
                continue
            current_coords = (p.point.y, p.point.x)
            if prev_point:
                prev_coords = (prev_point.point.y, prev_point.point.x)
                distance += geodesic(prev_coords, current_coords).km
            prev_point = p
        return round(distance, 2)

    def group_points(self, points):
        """Группирует точки по дню или месяцу в зависимости от report_type"""
        grouped = {}
        for p in points:
            if self.report_type == "daily":
                key = p.timestamp.date()
            elif self.report_type == "monthly":
                key = p.timestamp.strftime("%Y-%m")
            else:
                key = "all"
            grouped.setdefault((p.vehicle.plate_number, key), []).append(p)
        return grouped

    def build_report(self, points, limit=None):
        grouped = self.group_points(points)
        distance = 0
        results = []
        for (plate_number, period), pts in grouped.items():
            distance += self.calculate_distance(pts)
            if distance == 0 or (limit is not None and distance < limit):
                continue
            results.append(
                {
                    "vehicle": plate_number,
                    "duration": str(period),
                    "value": distance,
                    "report_type": self.report_type,
                }
            )
        return results


class EnterpriseDailyReportAPIView(BaseFleetReportAPIView):
    report_type = "daily"

    def get_cache_key(self, request, limit):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"enterprise_daily:{user.id}:{vehicle_ids}:{start}:{end}:{limit}"

    def get(self, request):
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        limit = request.GET.get("limit")
        if limit is not None:
            try:
                limit = float(limit)
            except ValueError:
                return Response(
                    {"detail": "Лимит пробега должен быть числом"}, status=400
                )
        cache_key = self.get_cache_key(request, limit)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)



        results = self.build_report(points, limit=limit)
        cache.set(cache_key, results, timeout=300)

        return Response(results)


class EnterpriseMonthlyReportAPIView(BaseFleetReportAPIView):
    report_type = "monthly"

    def get_cache_key(self, request, limit):
        user = request.user

        vehicle_ids = ",".join(sorted(request.GET.getlist("vehicle_ids")))
        start = request.GET.get("start")
        end = request.GET.get("end")

        return f"enterprise_daily:{user.id}:{vehicle_ids}:{start}:{end}:{limit}"

    def get(self, request):
        points = self.get_filtered_points(request)
        if isinstance(points, Response):
            return points

        limit = request.GET.get("limit")
        if limit is not None:
            try:
                limit = float(limit)
            except ValueError:
                return Response(
                    {"detail": "Лимит пробега должен быть числом"}, status=400
                )

        cache_key = self.get_cache_key(request, limit)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        results = self.build_report(points, limit=limit)
        cache.set(cache_key, results, timeout=300)
        return Response(results)


class UserEnterprisesAPIView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        if hasattr(user, "managers"):
            manager = user.managers
            enterprises = Enterprise.objects.filter(managers=manager)
        data = [{"id": e.id, "name": e.name} for e in enterprises]

        return Response(data)


class ImportGPXView(View):
    def post(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        file = request.FILES.get("gpx_file")

        if not file:
            messages.error(request, "Файл не выбран")
            return redirect("ui_vehicle_details", pk=vehicle.id)

        if not file.name.lower().endswith(".gpx"):
            messages.error(request, "Файл должен быть в формате GPX")
            return redirect("ui_vehicle_details", pk=vehicle.id)

        try:
            gpx = gpxpy.parse(file)

            if not gpx.tracks:
                messages.error(request, "GPX файл не содержит треков")
                return redirect("ui_vehicle_details", pk=vehicle.id)

            created = 0

            for track in gpx.tracks:
                for segment in track.segments:

                    processed_points = []

                    for point in segment.points:
                        if not point.time:
                            continue

                        timestamp = point.time
                        processed_points.append(
                            {
                                "lat": point.latitude,
                                "lng": point.longitude,
                                "timestamp": timestamp,
                            }
                        )

                    if not processed_points:
                        messages.warning(request, "Сегмент без валидных точек пропущен")
                        continue

                    processed_points.sort(key=lambda x: x["timestamp"])

                    start_ts = processed_points[0]["timestamp"]
                    end_ts = processed_points[-1]["timestamp"]

                    overlap_exists = VehicleTrip.objects.filter(
                        vehicle=vehicle,
                        start_timestamp__lte=end_ts,
                        end_timestamp__gte=start_ts,
                    ).exists()

                    if overlap_exists:
                        messages.warning(
                            request,
                            f"Пропущена поездка ({start_ts} - {end_ts}) — пересечение с существующей",
                        )
                        continue

                    trip = VehicleTrip.objects.create(
                        vehicle=vehicle,
                        start_timestamp=start_ts,
                        end_timestamp=end_ts,
                    )

                    track_points = []
                    skipped_duplicates = 0

                    for p in processed_points:
                        exists = VehicleTrackPoint.objects.filter(
                            vehicle=vehicle,
                            timestamp=p["timestamp"],
                        ).exists()

                        if exists:
                            skipped_duplicates += 1
                            continue

                        track_points.append(
                            VehicleTrackPoint(
                                vehicle=vehicle,
                                point=GEOSPoint(p["lng"], p["lat"], srid=4326),
                                timestamp=p["timestamp"],
                            )
                        )

                    if not track_points:
                        messages.warning(
                            request,
                            "Все точки оказались дубликатами — поездка пропущена",
                        )
                        trip.delete()
                        continue

                    VehicleTrackPoint.objects.bulk_create(track_points)

                    created += 1

            messages.success(request, f"Импортировано поездок: {created}")

        except Exception as e:
            messages.error(request, f"Ошибка GPX импорта: {str(e)}")

        return redirect("ui_vehicle_details", pk=vehicle.id)


class PageWithButtonView(View):
    """
    Возвращает страницу с кнопкой
    """

    def get(self, request):
        template = loader.get_template('vehicles/index.html')
        return HttpResponse(template.render({}, request))


class CurrentDatetimeView(View):
    """
    Возвращает текущую дату и время
    """

    def get(self, request):
        return HttpResponse(datetime.now())


@method_decorator(csrf_exempt, name='dispatch')
class SaveClientLogView(View):

    def post(self, request):
        logs = request.POST.get('logs', '[]')

        with open('request.log', 'a') as f:
            for log_str in json.loads(logs):
                f.write(json.dumps(log_str) + '\n')

        return HttpResponse()



# class DemoAllLatestPointsView(View):
#
#     authentication_classes = [SessionAuthentication, JWTAuthentication]
#     permission_classes = [IsAuthenticated]
#
#     async def get(self, request):
#
#         @sync_to_async(thread_sensitive=True)
#         def get_latest_points():
#             latest_ids = (
#                 VehicleTrackPoint.objects
#                 .values("vehicle_id")
#                 .annotate(max_id=Max("id"))
#             )
#
#             ids = [x["max_id"] for x in latest_ids]
#
#             qs = VehicleTrackPoint.objects.filter(id__in=ids)
#
#
#             return [
#                 {
#                     "vehicle_id": p.vehicle_id,
#                     "lat": p.point.y,
#                     "lng": p.point.x,
#                 }
#                 for p in qs
#             ]
#
#         data = await get_latest_points()
#
#         return JsonResponse({
#             "ok": True,
#             "points": data
#         })


class DemoAllLatestPointsView(View):

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    async def get(self, request):

        @sync_to_async(thread_sensitive=True)
        def get_latest_points():

            t0 = perf_counter()

            latest_ids = (
                VehicleTrackPoint.objects
                .values("vehicle_id")
                .annotate(max_id=Max("id"))
            )

            t1 = perf_counter()

            ids = [x["max_id"] for x in latest_ids]

            t2 = perf_counter()

            qs = VehicleTrackPoint.objects.filter(id__in=ids)

            t3 = perf_counter()

            data = [
                {
                    "vehicle_id": p.vehicle_id,
                    "lat": p.point.y,
                    "lng": p.point.x,
                }
                for p in qs
            ]

            t4 = perf_counter()

            print(
                f"""
-----------------------------
latest_ids queryset : {(t1 - t0) * 1000:.2f} ms
ids list           : {(t2 - t1) * 1000:.2f} ms
second queryset    : {(t3 - t2) * 1000:.2f} ms
serialize          : {(t4 - t3) * 1000:.2f} ms
total              : {(t4 - t0) * 1000:.2f} ms
-----------------------------
"""
            )

            return data

        t0 = perf_counter()

        data = await get_latest_points()

        t1 = perf_counter()

        response = JsonResponse({
            "ok": True,
            "points": data
        })

        t2 = perf_counter()

        print(
            f"""
=========== VIEW ===========
sync_to_async : {(t1 - t0) * 1000:.2f} ms
JsonResponse  : {(t2 - t1) * 1000:.2f} ms
TOTAL VIEW    : {(t2 - t0) * 1000:.2f} ms
============================
"""
        )

        return response

class DemoMapView(View):

    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    async def get(self, request):
        return render(request, "demo_map.html")