"""
URL configuration for TaxiTracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from vehicles.views import (VehiclesApiView, BrandsApiView, VehiclesDetailApiView,
                            DriversApiView, EnterprisesApiView, DriversDetailApiView, EnterprisesDetailApiView,
                            ManagersApiView, ManagersDetailApiView, UserLoginView, UserLogoutView, ManagerDashboardView, ManagerVehicleDashboardView,  ManagerVehicleCreateView, VehiclesBulkDeleteView, ManagerVehicleUpdateView, EnterpriseTimezoneUpdateView, SetTimezoneView,VehicleTrackAPIView, VehicleTripPointsRangeAPIView)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('dashboard/', ManagerDashboardView.as_view(), name='enterprise_detail'),
    path('vehicles_dashboard/<int:pk>/', ManagerVehicleDashboardView.as_view(), name='vehicles'),
    path('vehicle_details/<int:pk>/', ManagerVehicleUpdateView.as_view(), name='ui_vehicle_details'),
    path('vehicle_create/', ManagerVehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles_bulk_delete/', VehiclesBulkDeleteView.as_view(), name='vehicles_bulk_delete'),
    path("enterprise/<int:pk>/timezone/",EnterpriseTimezoneUpdateView.as_view(),name="update_enterprise_timezone"),
    path('set-timezone/', SetTimezoneView.as_view(), name='set_timezone'),

    path('api/v1/brands/<int:page>/', BrandsApiView.as_view()),
    path('api/v1/vehicles/', VehiclesApiView.as_view()),
    path('api/v1/drivers/<int:page>/', DriversApiView.as_view()),
    path('api/v1/enterprises/<int:page>/', EnterprisesApiView.as_view()),
    path('api/v1/managers/<int:page>/', ManagersApiView.as_view()),
    path('api/v1/drivers/<int:pk>/', DriversDetailApiView.as_view(), name='driver_detail'),
    path('api/v1/enterprises/<int:pk>/', EnterprisesDetailApiView.as_view(), name='enterprise_detail'),
    path('api/v1/vehicles/<int:pk>/', VehiclesDetailApiView.as_view(), name='vehicle_detail'),
    path('api/v1/managers/<int:pk>/', ManagersDetailApiView.as_view(), name='manager_detail'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/vehicle-track/', VehicleTrackAPIView.as_view(), name='vehicle-track'),
    path('api/v1/vehicle_trips/<int:pk>/points/', VehicleTripPointsRangeAPIView.as_view(), name='vehicle-trips'),
]


