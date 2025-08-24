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

from vehicles.views import VehiclesApiView, BrandsApiView, VehiclesDetailApiView, DriversApiView, EnterprisesApiView, DriversDetailApiView, EnterprisesDetailApiView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/brands/', BrandsApiView.as_view()),
    path('api/v1/vehicles/', VehiclesApiView.as_view()),
    path('api/v1/drivers/', DriversApiView.as_view()),
    path('api/v1/enterprises/', EnterprisesApiView.as_view()),
    path('api/v1/drivers/<int:id>/', DriversDetailApiView.as_view(), name = 'object_detail'),
    path('api/v1/enterprises/<int:id>/', EnterprisesDetailApiView.as_view(), name = 'object_detail'),
    path('api/v1/vehicles/<int:id>/', VehiclesDetailApiView.as_view(), name = 'object_detail'),
]
