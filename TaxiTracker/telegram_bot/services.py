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

logger = logging.getLogger(__name__)
ASK_USERNAME, ASK_PASSWORD = range(2)

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


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Для авторизации менеджера введите команду /login <username> <password>")
            return

        username, password = args
        user = await check_manager(username, password)
        if user:
            await update.message.reply_text(f"Привет, {user.get_full_name()}! Авторизация успешна ✅")
        else:
            await update.message.reply_text("Неверный логин или пароль ❌")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


# === Настройка бота ===
def setup_bot():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Асинхронно устанавливаем команды в меню
    async def set_commands(app):
        from telegram import BotCommand
        commands = [
            BotCommand("start", "Начать взаимодействие"),
            BotCommand("login", "Авторизация менеджера"),
            BotCommand("help", "Показать справку"),
            BotCommand("profile", "Показать информацию о профиле")
        ]
        await app.bot.set_my_commands(commands)

    application.post_init = set_commands

    return application