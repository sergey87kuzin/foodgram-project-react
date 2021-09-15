from rest_framework import permissions


class IsAuthorPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in ['put', 'delete']:
            return (
                obj.author.id == request.user.id
                or request.user.is_staff
            )
        return True
