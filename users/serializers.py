from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "jems",
            "total_xp",
            "streak_days",
            "last_activity",
        ]
        read_only_fields = ["jems", "total_xp", "streak_days", "last_activity"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "role",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
            "email": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(**validated_data)
        return user
