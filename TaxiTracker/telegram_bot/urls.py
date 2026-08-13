from django.urls import path
from . import views

urlpatterns = [
path('send-message/', views.send_telegram_message, name='send_message'),
]

# project/urls.py
from django.urls import path, include

urlpatterns = [
    path("send-message/", views.send_telegram_message, name="send_message"),
    path("prometheus-alert/", views.prometheus_alert, name="prometheus_alert"),
]