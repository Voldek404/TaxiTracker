import logging
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from django.conf import settings
from django.contrib.auth import authenticate
from .models import TelegramProfile
from telegram.ext import ConversationHandler, MessageHandler, filters
import httpx
import calendar
from rest_framework.response import Response
from datetime import datetime, timedelta




logger = logging.getLogger(__name__)

application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()


@sync_to_async(thread_sensitive=True)
def save_profile(user):
    return TelegramProfile.objects.update_or_create(
        telegram_id=user.id,
        defaults={
            'username': user.username,  # Telegram username
            'first_name': user.first_name,  # Имя из Telegram
            'last_name': user.last_name,  # Фамилия из Telegram
            'is_bot': user.is_bot,
            'language_code': user.language_code,
        }
    )


@sync_to_async(thread_sensitive=True)
def get_profile(user_id):
    return TelegramProfile.objects.get(telegram_id=user_id)

@sync_to_async(thread_sensitive=True)
def check_manager(username, password):
    user = authenticate(username=username, password=password)
    return user


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await save_profile(user)

    welcome_text = f"Привет, {user.first_name}! Я бот для работы с маршрутизатором автопарков."

    keyboard = [
        [InlineKeyboardButton("Мой профиль", callback_data="profile")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "profile":
        user = update.effective_user
        profile = await get_profile(user.id)

        profile_text = (
            f"🔑 ID: {profile.telegram_id}\n"
            f"👤 Имя: {profile.first_name} {profile.last_name}\n"
            f"👤 Username: @{profile.username}\n"
            f"🌍 Язык: {profile.language_code}\n"
        )
        await query.edit_message_text(text=profile_text)

    elif query.data == "help":
        help_text = (
            "Доступные команды:\n"
            "/start – Начать взаимодействие\n"
            "/profile – Показать информацию о профиле\n"
            "/login – Авторизация менеджера\n"
            "/help – Показать эту справку"
        )
        await query.edit_message_text(text=help_text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Эхо: {text}")

ASK_USERNAME, ASK_PASSWORD = range(2)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите логин:")
    return ASK_USERNAME


async def login_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data["username"] = username

    await update.message.reply_text("Введите пароль:")
    return ASK_PASSWORD


async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text
    username = context.user_data.get("username")

    user = await check_manager(username, password)

    if user:
        url = "http://127.0.0.1:8000/api/v1/token/"
        data = {
            "username": username,
            "password": password
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            if response.status_code == 200:
                token = response.json().get("access")
                context.user_data["token"] = token
                await update.message.reply_text(
                    f"Привет, {user.get_full_name()}! Авторизация успешна , Токен для api получен"
                )
            else:
                await update.message.reply_text("Неверный логин или пароль , введите команду /login заново")

    return ConversationHandler.END


async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Авторизация отменена ")
    return ConversationHandler.END

login_handler = ConversationHandler(
    entry_points=[CommandHandler("login", login_command)],
    states={
        ASK_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, login_username)
        ],
        ASK_PASSWORD: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)
        ],
    },
    fallbacks=[CommandHandler("cancel", login_cancel)],
)


ASK_VEHICLE_ID, ASK_MONTH = range(2)

async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Введите месяц в формате YYYY-MM или MM-YYYY (например 2026-02 или 02-2026):")
    return ASK_MONTH

async def ask_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    month_text = update.message.text.strip()
    try:
        year, month = map(int, month_text.split("-"))
        if not (1 <= month <= 12) or not (2024 <= year <= 2026):
            raise ValueError
    except ValueError:
        try:
            month, year = map(int, month_text.split("-"))
            if not (1 <= month <= 12) or not (2024 <= year <= 2026):
                raise ValueError
        except ValueError:
            await update.message.reply_text("Неверный формат. Пример: 2026-02 или 02-2026")
            return ASK_MONTH

    context.user_data["month"] = f"{year:04d}-{month:02d}"
    await update.message.reply_text("Введите ID машины:")
    return ASK_VEHICLE_ID

async def get_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_id = update.message.text.strip()
    user = context.user_data.get("username")
    report_month = context.user_data.get("month")
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    year, month = map(int, report_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]

    url = "http://127.0.0.1:8000/api/v1/reports/monthly/"

    params = {
        "vehicle_ids": car_id,
        "start": f"{report_month}-01",
        "end": f"{report_month}-{last_day}",
        "type": "monthly",
    }

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

        if response.status_code == 403:
            await update.message.reply_text("Нет доступа к этой машине")
            return ConversationHandler.END

        if response.status_code != 200:
            await update.message.reply_text(" Ошибка при получении отчёта")
            return ConversationHandler.END

        data = response.json()

        if not data:
            await update.message.reply_text("📭 Нет данных за этот период")
            return ConversationHandler.END

        text = " Месячный отчёт:\n\n"

        for item in data:
            text += (
                f"{item['vehicle']}\n"
                f"{item['duration']}\n"
                f"Пробег: {item['value']} км\n\n"
            )

        await update.message.reply_text(text)

    except httpx.RequestError:
        await update.message.reply_text(" Ошибка соединения с сервером")

    return ConversationHandler.END


monthly_handler = ConversationHandler(
    entry_points=[CommandHandler("monthly_report", start_report)],
    states={
        ASK_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_month)],
        ASK_VEHICLE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_monthly_report)],
    },
    fallbacks=[],
)

ASK_DAILY_VEHICLE_ID, ASK_DAY = range(2,4)

async def start_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Введите дату в формате YYYY-MM-DD (например 2026-02-01 или 01-02-2026):")
    return ASK_DAY

async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text.strip()
    try:
        year, month, day = map(int, date_text.split("-"))
        if not (1 <= month <= 12) or not (1 <= day <= 31) or not (2024 <= year <= 2026):
            raise ValueError
    except ValueError:
        try:
            day, month, year = map(int, date_text.split("-"))
            if not (1 <= month <= 12) or not (1 <= day <= 31) or not (2024 <= year <= 2026):
                raise ValueError
        except ValueError:
            await update.message.reply_text(" Неверный формат. Пример: 2026-02-01 или 01-02-2026")
            return ASK_DAY

    context.user_data["date"] = f"{year:04d}-{month:02d}-{day:02d}"
    await update.message.reply_text("Введите ID машины:")
    return ASK_DAILY_VEHICLE_ID

async def get_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_id = update.message.text.strip()
    user = context.user_data.get("username")
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    date_text= context.user_data.get("date")
    url = "http://127.0.0.1:8000/api/v1/reports/daily/"
    date_obj = datetime.strptime(date_text, "%Y-%m-%d")
    next_day = date_obj + timedelta(days=1)

    params = {
        "vehicle_ids": car_id,
        "start": date_obj.strftime("%Y-%m-%d"),
        "end": next_day.strftime("%Y-%m-%d"),
        "type": "daily",
    }

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)

        if response.status_code == 403:
            await update.message.reply_text("Нет доступа к этой машине")
            return ConversationHandler.END

        if response.status_code != 200:
            await update.message.reply_text(" Ошибка при получении отчёта")
            return ConversationHandler.END

        data = response.json()

        if not data:
            await update.message.reply_text(" Нет данных за этот период")
            return ConversationHandler.END

        text = f" Отчет за сутки {data}:\n\n"

        for item in data:
            text += (
                f"{item['vehicle']}\n"
                f"{item['duration']}\n"
                f"Пробег: {item['value']} км\n\n"
            )

        await update.message.reply_text(text)

    except httpx.RequestError:
        await update.message.reply_text(" Ошибка соединения с сервером")

    return ConversationHandler.END


daily_handler = ConversationHandler(
    entry_points=[CommandHandler("daily_report", start_daily_report)],
    states={
        ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
        ASK_DAILY_VEHICLE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_daily_report)],
    },
    fallbacks=[],
)


# === Настройка бота ===
def setup_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Регистрация команд
    application.add_handler(login_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))

    application.add_handler(monthly_handler)
    application.add_handler(daily_handler)
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Асинхронно устанавливаем команды в меню
    async def set_commands(app):
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Начать взаимодействие"),
            BotCommand("login", "Авторизация менеджера"),
            BotCommand("help", "Показать справку"),
            BotCommand("profile", "Показать информацию о профиле"),
            BotCommand("monthly_report", "Показать пробег за месяц"),
            BotCommand("daily_report", "Показать пробег за сутки"),
        ]
        await app.bot.set_my_commands(commands)

    application.post_init = set_commands

    return application