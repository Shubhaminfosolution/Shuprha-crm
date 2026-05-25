from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdmin
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes



class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Admin sees all users
        if user.role == "admin":
            return User.objects.filter(is_active=True, is_deleted=False)
        # Others only see internal team members for assignee dropdown
        return User.objects.filter(
            is_active=True,
            is_deleted=False,
            role__in=["admin", "manager", "sales"]
        )

    def get_permissions(self):
        # Only admin can create/update/delete users
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)