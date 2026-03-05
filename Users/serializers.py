from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only = True)

    class meta:
        models = User
        fields = ["id", "email","full_name", "role", "password"]

        def create(self, validated_data):
            password = validated_data.pop("password")
            user = User.objects.create(**validated_data)
            user.set_password(password)
            user.save()
            return user
        
