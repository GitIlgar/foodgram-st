from rest_framework import permissions as perms


class IsAuthorOrReadOnly(perms.BasePermission):

    def has_object_permission(self, request, view, obj):
        return (
            request.method in perms.SAFE_METHODS
            or obj.author == request.user
        )
