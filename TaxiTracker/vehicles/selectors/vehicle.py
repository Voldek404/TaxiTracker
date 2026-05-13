from vehicles.models import Enterprise


from vehicles.models import Vehicle


def get_manager_vehicles(manager):

    return Vehicle.objects.filter(
        enterprise__in=manager.enterprises.all(),
    )