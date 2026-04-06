import logging
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from django.conf import settings
from django.contrib.auth import authenticate
from .models import TelegramProfile
from vehicles.models import Manager, Enterprise
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
    await update.message.reply_text("Введите регистрационный номер ТС:")
    return ASK_VEHICLE_ID

async def get_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_plate_number = update.message.text.strip()
    user = context.user_data.get("username")
    report_month = context.user_data.get("month")
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    year, month = map(int, report_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]

    url = "http://127.0.0.1:8000/api/v1/tg-reports/monthly/"

    params = {
        "vehicle_pns": car_plate_number,
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

async def get_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    car_plate_number = update.message.text.strip()
    user = context.user_data.get("username")
    report_month = context.user_data.get("month")
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    year, month = map(int, report_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]

    url = "http://127.0.0.1:8000/api/v1/tg-reports/monthly/"

    params = {
        "vehicle_pns": car_plate_number,
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


ASK_ENTERPRISE, ASK_DAY, ASK_LIMIT = range(3)

async def fetch_user_enterprises(token):
    url = "http://127.0.0.1:8000/api/v1/tg-reports/user-enterprises/"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return None

    return response.json()


async def start_fleet_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = context.user_data.get("token")

    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    enterprises = await fetch_user_enterprises(token)

    if not enterprises:
        await update.message.reply_text("📭 У вас нет автопарков")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(ent["name"], callback_data=str(ent["id"]))]
        for ent in enterprises
    ]

    await update.message.reply_text(
        "📋 Выберите автопарк:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return ASK_ENTERPRISE


async def daily_enterprise_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["enterprise_id"] = int(query.data)

    await query.message.reply_text("📅 Введите дату (YYYY-MM-DD):")
    return ASK_DAY


async def daily_ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        date_obj = datetime.strptime(update.message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат даты")
        return ASK_DAY

    context.user_data["date"] = date_obj.strftime("%Y-%m-%d")

    await update.message.reply_text("Введите лимит пробега (км):")
    return ASK_LIMIT


async def daily_ask_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Введите число")
        return ASK_LIMIT

    token = context.user_data.get("token")
    enterprise_id = context.user_data.get("enterprise_id")
    date_text = context.user_data.get("date")

    date_obj = datetime.strptime(date_text, "%Y-%m-%d")
    next_day = date_obj + timedelta(days=1)

    url = "http://127.0.0.1:8000/api/v1/tg-reports/daily-ent/"

    params = {
        "enterprise_id": enterprise_id,
        "start": date_obj.strftime("%Y-%m-%d"),
        "end": next_day.strftime("%Y-%m-%d"),
        "limit": int(limit)
    }

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers=headers,
            timeout=10.0
        )

    if response.status_code != 200:
        await update.message.reply_text("❌ Ошибка отчёта")
        return ConversationHandler.END

    data = response.json()

    if not data:
        await update.message.reply_text("📭 Нет данных")
        return ConversationHandler.END

    text = f"📊 Отчет за {date_text}:\n\n"

    for item in data:
        dist = int(item["value"])
        if dist < limit:
            text += f"{item['vehicle']}: {dist} км ❌ ниже лимита\n"
        else:
            text += f"{item['vehicle']}: {dist} км\n"

    await update.message.reply_text(text)
    return ConversationHandler.END

fleet_daily_handler = ConversationHandler(
    entry_points=[CommandHandler("fleet_daily_report", start_fleet_daily)],
    states={
        ASK_ENTERPRISE: [CallbackQueryHandler(daily_enterprise_chosen)],
        ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, daily_ask_day)],
        ASK_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, daily_ask_limit)],
    },
    fallbacks=[],
)


ASK_MONTHLY_ENTERPRISE, ASK_MONTHLY_PERIOD, ASK_MONTHLY_LIMIT = range(10, 13)


# === шаг 1: выбрать автопарк ===
async def start_fleet_monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = context.user_data.get("token")
    if not token:
        await update.message.reply_text("❗ Сначала авторизуйтесь (/login)")
        return ConversationHandler.END

    enterprises = await fetch_user_enterprises(token)
    if not enterprises:
        await update.message.reply_text("📭 У вас нет автопарков")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton(ent["name"], callback_data=str(ent["id"]))] for ent in enterprises]

    await update.message.reply_text(
        "📋 Выберите автопарк:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_MONTHLY_ENTERPRISE


# === шаг 2: автопарк выбран ===
async def monthly_enterprise_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_reply_markup(None)

    try:
        context.user_data["enterprise_id"] = int(query.data)
    except ValueError:
        await query.message.reply_text("❌ Неверный выбор автопарка")
        return ConversationHandler.END

    await query.message.reply_text("📅 Введите месяц для отчёта в формате YYYY-MM:")
    return ASK_MONTHLY_PERIOD


# === шаг 3: месяц выбран ===
async def monthly_ask_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        selected_month = datetime.strptime(text, "%Y-%m")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат месяца. Используйте YYYY-MM")
        return ASK_MONTHLY_PERIOD

    context.user_data["month"] = selected_month
    await update.message.reply_text("Введите лимит пробега (км):")
    return ASK_MONTHLY_LIMIT


# === шаг 4: лимит введён, формируем отчёт ===
async def monthly_get_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        limit = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Введите число")
        return ASK_MONTHLY_LIMIT

    token = context.user_data.get("token")
    enterprise_id = context.user_data.get("enterprise_id")
    month_obj = context.user_data.get("month")

    start = month_obj.replace(day=1).strftime("%Y-%m-%d")
    last_day = calendar.monthrange(month_obj.year, month_obj.month)[1]
    end = month_obj.replace(day=last_day).strftime("%Y-%m-%d")

    url = "http://127.0.0.1:8000/api/v1/tg-reports/monthly-ent/"

    params = {
        "enterprise_id": enterprise_id,
        "start": start,
        "end": end,
    }
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers=headers,
            timeout=20.0
        )

    if response.status_code != 200:
        await update.message.reply_text("❌ Ошибка отчёта")
        return ConversationHandler.END

    data = response.json()
    if not data:
        await update.message.reply_text("📭 Нет данных")
        return ConversationHandler.END

    text = f"📊 Отчёт за {month_obj.strftime('%B %Y')}:\n\n"
    for item in data:
        dist = int(item["value"])
        if dist < limit:
            continue
        text += f"{item['vehicle']}: {dist} км\n"

    if text == f"📊 Отчёт за {month_obj.strftime('%B %Y')}:\n\n":
        text += "Нет машин, превышающих лимит"

    await update.message.reply_text(text)
    return ConversationHandler.END


# === Monthly ConversationHandler ===
fleet_monthly_handler = ConversationHandler(
    entry_points=[CommandHandler("fleet_monthly_report", start_fleet_monthly)],
    states={
        ASK_MONTHLY_ENTERPRISE: [CallbackQueryHandler(monthly_enterprise_chosen)],
        ASK_MONTHLY_PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, monthly_ask_period)],
        ASK_MONTHLY_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, monthly_get_report)],
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

    # Существующие отчеты
    application.add_handler(monthly_handler)
    application.add_handler(fleet_daily_handler)

    # Новый отчёт по автопарку
    application.add_handler(fleet_monthly_handler)

    # Обработчики кнопок и текста
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
            BotCommand("fleet_monthly_report", "Месячный отчёт по автопарку"),
            BotCommand("fleet_daily_report", "Пробег всех машин автопарка за день"),
        ]
        await app.bot.set_my_commands(commands)

    application.post_init = set_commands

    return application