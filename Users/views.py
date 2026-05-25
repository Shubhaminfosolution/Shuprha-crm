from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdmin
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes



class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin] 

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    from .serializers import UserSerializer
    return Response(UserSerializer(request.user).data)