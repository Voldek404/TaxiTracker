import asyncio
import json
import logging

from confluent_kafka import Consumer
from django.conf import settings
from django.core.management.base import BaseCommand

from telegram_bot.services import setup_bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Kafka consumer for Telegram notifications"

    def handle(self, *args, **options):

        asyncio.run(self.consume())

    async def consume(self):

        application = setup_bot()

        await application.initialize()

        consumer = Consumer(
            {
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": "telegram-consumer",
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

        consumer.subscribe(
            [
                "telegram.notifications"
            ]
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Kafka consumer started..."
            )
        )

        try:
            while True:

                msg = consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    logger.error(
                        "Kafka error: %s",
                        msg.error()
                    )
                    continue

                try:

                    payload = json.loads(
                        msg.value().decode("utf-8")
                    )

                    logger.info(
                        "Kafka message received: %s",
                        payload
                    )

                    telegram_id = payload.get(
                        "telegram_id"
                    )

                    message = payload.get(
                        "message"
                    )


                    if not telegram_id:
                        logger.error(
                            "Missing telegram_id: %s",
                            payload
                        )
                        consumer.commit(msg)
                        continue


                    if not message:
                        logger.error(
                            "Missing message text: %s",
                            payload
                        )
                        consumer.commit(msg)
                        continue


                    try:

                        telegram_id = int(
                            telegram_id
                        )

                    except ValueError:

                        logger.error(
                            "Invalid telegram_id: %s",
                            telegram_id
                        )

                        consumer.commit(msg)
                        continue


                    await application.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                    )


                    logger.info(
                        "Telegram notification sent: %s",
                        telegram_id
                    )


                    consumer.commit(msg)


                except Exception:

                    logger.exception(
                        "Notification processing failed"
                    )


        except KeyboardInterrupt:

            self.stdout.write(
                "Consumer stopped."
            )


        finally:

            consumer.close()

            await application.shutdown()