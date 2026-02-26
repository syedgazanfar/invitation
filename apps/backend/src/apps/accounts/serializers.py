"""
Serializers for User Accounts
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'username', 'email', 'full_name',
            'is_phone_verified', 'is_blocked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_phone_verified', 'is_blocked', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    active_orders_count = serializers.IntegerField(read_only=True)
    total_invitations = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'username', 'email', 'full_name',
            'is_phone_verified', 'created_at', 'updated_at',
            'active_orders_count', 'total_invitations'
        ]
        read_only_fields = ['id', 'phone', 'is_phone_verified', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['phone', 'username', 'email', 'full_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_phone(self, value):
        # Remove spaces and validate format
        phone = value.replace(' ', '').replace('-', '')
        if not phone.startswith('+91'):
            phone = '+91' + phone[-10:]
        
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        
        return phone
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        
        # Normalize phone number
        phone = validated_data['phone'].replace(' ', '').replace('-', '')
        if not phone.startswith('+91'):
            phone = '+91' + phone[-10:]
        validated_data['phone'] = phone
        
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login - accepts username or phone"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class OTPSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone = serializers.CharField(required=True)
    otp = serializers.CharField(required=True, min_length=6, max_length=6)


class PhoneOnlySerializer(serializers.Serializer):
    """Serializer for phone-only requests"""
    phone = serializers.CharField(required=True)


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
