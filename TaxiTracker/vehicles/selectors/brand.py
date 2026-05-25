from vehicles.models import Brand, Enterprise

def get_user_brands(user):
    manager = getattr(user, "managers", None)

    if not manager:
        return Brand.objects.none()

    return Brand.objects.filter(
        vehicles__enterprise__in=manager.enterprises.all()
    ).distinct()