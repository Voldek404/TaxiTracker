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
                            DriversApiView, EnterprisesApiView, DriversDetailApiView, EnterprisesDetailApiView,ManagersApiView,ManagersDetailApiView )
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/brands/', BrandsApiView.as_view()),
    path('api/v1/vehicles/', VehiclesApiView.as_view()),
    path('api/v1/drivers/', DriversApiView.as_view()),
    path('api/v1/enterprises/', EnterprisesApiView.as_view()),
    path('api/v1/managers/', ManagersApiView.as_view()),
    path('api/v1/drivers/<int:pk>/', DriversDetailApiView.as_view(), name='driver_detail'),
    path('api/v1/enterprises/<int:pk>/', EnterprisesDetailApiView.as_view(), name='enterprise_detail'),
    path('api/v1/vehicles/<int:pk>/', VehiclesDetailApiView.as_view(), name='vehicle_detail'),
    path('api/v1/managers/<int:pk>/', ManagersDetailApiView.as_view(), name='manager_detail'),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]