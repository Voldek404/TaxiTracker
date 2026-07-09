from .producer import producer
import json
import logging

logger = logging.getLogger(__name__)


def send_telegram_notification(telegram_id: int, message: str):

    data = {
        "telegram_id": telegram_id,
        "message": message,
    }

    logger.info(
        "Sending Kafka notification: %s",
        data
    )

    try:
        producer.produce(
            "telegram.notifications",
            json.dumps(data).encode("utf-8")
        )

        producer.flush()

        logger.info(
            "Kafka notification sent"
        )

    except Exception:
        logger.exception(
            "Kafka send failed"
        )