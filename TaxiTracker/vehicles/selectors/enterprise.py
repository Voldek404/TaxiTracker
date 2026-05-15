from vehicles.models import Enterprise


def get_user_enterprises(user):

    manager = getattr(
        user,
        "managers",
        None,
    )

    if not manager:
        return Enterprise.objects.none()

    return manager.enterprises.all()