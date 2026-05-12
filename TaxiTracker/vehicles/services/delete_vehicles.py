
from django.db import transaction
from django.core.exceptions import ValidationError
from vehicles.models import Vehicle


@transaction.atomic
def delete_vehicles(vehicle_ids: list[int]):

    vehicles = Vehicle.objects.filter(id__in=vehicle_ids)

    if vehicles.filter(driver__isnull=False).exists():
        raise ValidationError(
            "Нельзя удалить автомобили с водителем"
        )

    deleted_count = vehicles.count()
    vehicles.delete()

    return deleted_count