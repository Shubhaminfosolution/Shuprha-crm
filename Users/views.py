from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdmin



class UserViewSet(ModelViewSet):
    queryset = User.object.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin] 