from zoneinfo import ZoneInfo
from django.utils import timezone
import time
import json
from threading import local
import logging


thread_locals = local()


class RequestTimeMiddleware:
   def __init__(self, get_response):
       self.get_response = get_response

   def __call__(self, request):
       thread_locals.path = request.path
       thread_locals.sql_count = 0
       thread_locals.sql_total = 0
       timestamp = time.monotonic()

       response = self.get_response(request)

       data = {
           'uuid': request.META.get('HTTP_UUID'),
           'c_started': request.META.get('HTTP_C_STARTED'),
           'path': request.path,
           'request_total': round(time.monotonic() - timestamp, 3),
           'sql_count': thread_locals.sql_count,
           'sql_total': round(thread_locals.sql_total, 3),
       }

       for key, value in data.items():
           response[key.capitalize().replace("_", "-")] = value
       # #
       # with open('request.log', 'a') as f:
       #     f.write(json.dumps(data) + '\n')





       thread_locals.sql_total = 0
       thread_locals.sql_count = 0
       thread_locals.path = ''

       return response


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            return self.get_response(request)

        tzname = request.session.get("django_timezone")
        if tzname:
            timezone.activate(ZoneInfo(tzname))
        else:
            timezone.deactivate()

        return self.get_response(request)


logger = logging.getLogger("django")

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()

        response = self.get_response(request)

        duration = (time.time() - start) * 1000

        log_data = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round(duration, 2),
        }

        logger.info(json.dumps(log_data))

        return response

