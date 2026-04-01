
from django.db import models
from vehicles.models import Manager

class TelegramProfile(models.Model):
    objects = models.Manager()
    manager = models.OneToOneField(
        Manager,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    telegram_id = models.BigIntegerField(unique=True)

    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    is_bot = models.BooleanField(default=False)
    language_code = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        if self.manager:
            return f"{self.manager.full_name} ({self.telegram_id})"
        return f"Unlinked ({self.telegram_id})"