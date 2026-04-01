from django.urls import path
from . import views

urlpatterns = [
path('send-message/', views.send_message, name='send_message'),
]

# project/urls.py
from django.urls import path, include

urlpatterns = [
# ...
path('api/telegram/', include('telegram_bot.urls')),
# ...
]