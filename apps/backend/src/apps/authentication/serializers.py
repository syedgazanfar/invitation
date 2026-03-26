"""
Serializers for the authentication module.

Kept deliberately minimal: validation of business rules (wrong password,
blocked account, etc.) belongs in the service layer, not serializers.
"""
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Shared serializer for both user and admin login."""

    identifier = serializers.CharField(
        required=True,
        help_text='Username or phone number',
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_identifier(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('This field may not be blank.')
        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError('This field may not be blank.')
        return value


class AdminLoginSerializer(LoginSerializer):
    """Admin login — identical fields, separate class for clarity in URLs and docs."""
    pass


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text='Refresh token to blacklist',
    )


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text='Valid refresh token',
    )
