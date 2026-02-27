from rest_framework import permissions


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактировать только свой профиль.
    Просматривать — можно любой.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user
