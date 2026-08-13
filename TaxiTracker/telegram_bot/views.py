import asyncio
import json

import telegram

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import TelegramProfile


async def send_telegram_message(bot, chat_id, text):
    return await bot.send_message(
        chat_id=chat_id,
        text=text,
    )


@csrf_exempt
@require_POST
def prometheus_alert(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON"},
            status=400,
        )

    alerts = data.get("alerts", [])

    if not alerts:
        return JsonResponse(
            {"success": False, "error": "No alerts provided"},
            status=400,
        )

    bot = telegram.Bot(
        token=settings.TELEGRAM_BOT_TOKEN
    )

    profiles = TelegramProfile.objects.all()

    sent = 0

    async def send_all():
        nonlocal sent

        for alert in alerts:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})

            alert_name = labels.get(
                "alertname",
                "Unknown alert",
            )

            severity = labels.get(
                "severity",
                "unknown",
            )

            summary = annotations.get(
                "summary",
                "",
            )

            description = annotations.get(
                "description",
                "",
            )

            message = (
                f"🚨 PROMETHEUS ALERT\n\n"
                f"Alert: {alert_name}\n"
                f"Severity: {severity}\n\n"
                f"{summary}\n"
                f"{description}"
            )

            for profile in profiles:
                await bot.send_message(
                    chat_id=profile.telegram_id,
                    text=message,
                )

                sent += 1

    try:
        asyncio.run(send_all())
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )

    return JsonResponse(
        {
            "success": True,
            "alerts": len(alerts),
            "messages_sent": sent,
        }
    )
@csrf_exempt
def webhook(request):
    """
    Обработчик Webhook от Telegram
    """
    if request.method == 'POST':
        json_string = request.body.decode('utf-8')
        update = Update.de_json(json.loads(json_string), bot)
        dispatcher.process_update(update)
    return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

