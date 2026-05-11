from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["manager", "admin"]


class IsSales(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ["sales", "manager", "admin"]


class IsClient(BasePermission):
    """Business owner — has a business FK on their user."""
    def has_permission(self, request, view):
        return request.user.role == "client" and request.user.business is not None


class IsInternalOrClient(BasePermission):
    """Allows both internal staff and client users — used on shared endpoints."""
    def has_permission(self, request, view):
        return request.user.role in ["admin", "manager", "sales", "client"]


class IsAdminOrOwnBusiness(BasePermission):
    """
    Object-level permission.
    Admin can access any business object.
    Client can only access objects belonging to their own business.
    Usage: check_object_permissions(request, obj) where obj has a .business attribute.
    """
    def has_permission(self, request, view):
        return request.user.role in ["admin", "manager", "client"]

    def has_object_permission(self, request, view, obj):
        if request.user.role in ["admin", "manager"]:
            return True
        # For client — obj must have a .business attribute
        if request.user.role == "client":
            obj_business = getattr(obj, 'business', None)
            return obj_business == request.user.business
        return False