from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Vehicle, Driver

@receiver(post_save, sender=Vehicle)
def update_driver_activity(sender, instance, **kwargs):
    """
    Автоматически устанавливает is_active водителя при назначении на машину.
    """
    # Если водитель назначен
    if instance.driver:
        # Ставим активного текущего водителя
        instance.driver.is_active = True
        instance.driver.save()

        # Для всех остальных водителей на этом предприятии, кроме текущего, делаем is_active=False
        Driver.objects.filter(enterprise=instance.enterprise).exclude(id=instance.driver.id).update(is_active=False)

@receiver(pre_save, sender=Driver)
def deactivate_driver(sender, instance, **kwargs):
    if not instance.pk:
        # Новый водитель, игнорируем
        return
    previous = Driver.objects.get(pk=instance.pk)
    if previous.is_active and not instance.is_active:
        # Снимаем связь с машиной, где он был активным
        Vehicle.objects.filter(driver=instance).update(driver=None)