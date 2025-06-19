from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from api.controllers import user_controller

class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = user_controller.get_user_by_email(email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Usuario não existe.")

        user = authenticate(email=user.email, password=password)
        if not user:
            raise serializers.ValidationError("Email ou senha inválidos.")

        if not user.is_verified:
            raise serializers.ValidationError("E-mail ainda não confirmado.")

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
