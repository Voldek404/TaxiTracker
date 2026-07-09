from telegram_framework import (
    messages,
    actions,
    links,
)


def send_greetings(bot, message):
    greetings_message = messages.create_message(
        'Приветствую тебя. Я Quickstart Telegram Bot',
        sender=bot
    )
    return actions.send_message(message.chat, greetings_message)

def reply_to_message(bot, message):
    # Используйте специальную функцию для создания ответа
    reply = messages.create_reply(message, 'Тебе отвечает Bot', sender=bot)
    # Отправьте ответ в телеграмм
    return actions.send_reply(reply)


# СВЯЖИТЕ ОБРАБОТЧИКИ С ДЕЙСТВИЯМИ ПОЛЬЗОВАТЕЛЯ В TELEGRAM

bot_links = [
    links.on_command(send_greetings, 'start'),
    links.on_command(send_greetings, 'help'),
    links.on_message(reply_to_message),
]