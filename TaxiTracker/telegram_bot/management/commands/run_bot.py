from django.core.management.base import BaseCommand
from telegram_bot.services import setup_bot

class Command(BaseCommand):
    help = 'Запуск Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))
        bot = setup_bot()
        bot.run_polling()