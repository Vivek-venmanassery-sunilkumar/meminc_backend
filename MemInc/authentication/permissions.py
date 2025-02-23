from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsAuthenticatedAndNotBlocked(BasePermission):


    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            raise PermissionDenied("You must be logged in to access this resource.")
        
        if request.user.is_blocked:
            raise PermissionDenied("Your account has been blocked. Please contact support.")
        
        return True