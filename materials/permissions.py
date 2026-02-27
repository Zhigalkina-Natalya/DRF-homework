from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Разрешение, проверяющее, что пользователь входит в группу 'Модераторы'."""

    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.groups.filter(name="Модераторы").exists()
        )


class IsOwner(BasePermission):
    """Разрешение: доступ только владельцу объекта."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
