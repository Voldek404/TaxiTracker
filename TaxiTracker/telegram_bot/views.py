import telegram
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import TelegramProfile

@csrf_exempt
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        telegram_id = data.get('telegram_id')
        message = data.get('message')

        if not telegram_id or not message:
            return JsonResponse(
                {'success': False, 'error': 'Отсутствуют обязательные параметры'},
                status=400
            )

        # Проверка существования пользователя
        try:
            profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        except TelegramProfile.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': 'Пользователь не найден'},
                status=404
            )

        # Отправка сообщения
        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=telegram_id, text=message)

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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

