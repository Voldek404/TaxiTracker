from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from vehicles.models import Vehicle, Enterprise, VehicleTrip


class IsManager(BasePermission):

    def has_permission(self, request, view):
        if not hasattr(request.user, "managers"):
            return False
        return True


class HasEnterpriseAccess(BasePermission):

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, "managers"):
            return False

        return obj.enterprise in request.user.managers.enterprises.all()

class HasTripAccess(BasePermission):

    def has_object_permission(self, request, view, obj: VehicleTrip):
        if not hasattr(request.user, "managers"):
            return False

        return obj.vehicle.enterprise in request.user.managers.enterprises.all()


class CanDeleteVehicle(BasePermission):

    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.is_superuser
        return True


