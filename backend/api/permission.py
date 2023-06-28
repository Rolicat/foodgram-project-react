from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    """Проверка на авторство."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and request.user == obj.author
        )
