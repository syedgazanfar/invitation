"""
Views for the authentication module.

Endpoints
---------
POST /api/v1/auth/login/           User login (phone or username + password)
POST /api/v1/auth/admin/login/     Admin-only login (requires is_staff=True)
POST /api/v1/auth/logout/          Blacklist refresh token (authenticated)
POST /api/v1/auth/token/refresh/   Exchange refresh token for a new access token
"""
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AdminLoginSerializer,
    LoginSerializer,
    LogoutSerializer,
    TokenRefreshSerializer,
)
from .services import LoginService

logger = logging.getLogger(__name__)

# Map service error codes to HTTP status codes.
# Any code not listed here falls back to 400 Bad Request.
_ERROR_STATUS: dict = {
    'INVALID_CREDENTIALS': status.HTTP_401_UNAUTHORIZED,
    'ACCOUNT_BLOCKED':     status.HTTP_403_FORBIDDEN,
    'PENDING_APPROVAL':    status.HTTP_403_FORBIDDEN,
    'NOT_ADMIN':           status.HTTP_403_FORBIDDEN,
    'TOKEN_INVALID':       status.HTTP_401_UNAUTHORIZED,
    'VALIDATION_ERROR':    status.HTTP_400_BAD_REQUEST,
    'SERVER_ERROR':        status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def _error_response(code: str, message: str) -> Response:
    http_status = _ERROR_STATUS.get(code, status.HTTP_400_BAD_REQUEST)
    return Response(
        {'success': False, 'code': code, 'message': message},
        status=http_status,
    )


class UserLoginView(APIView):
    """
    POST /api/v1/auth/login/

    Body:
        identifier  string  Username or phone number (required)
        password    string  Account password (required)

    Returns JWT access and refresh tokens on success.
    Regular users must be approved; staff and superusers bypass that check.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'code': 'VALIDATION_ERROR',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, data, code, message = LoginService.user_login(
            identifier=serializer.validated_data['identifier'],
            password=serializer.validated_data['password'],
            request=request,
        )

        if not success:
            return _error_response(code, message)

        return Response({
            'success': True,
            'code': code,
            'message': 'Login successful',
            'data': data,
        })


class AdminLoginView(APIView):
    """
    POST /api/v1/auth/admin/login/

    Body:
        identifier  string  Username or phone number (required)
        password    string  Account password (required)

    The account must have is_staff=True. Approval status is not checked
    for admin accounts. Returns an extended payload with permission flags.
    """
    permission_classes = [AllowAny]
    serializer_class = AdminLoginSerializer

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'code': 'VALIDATION_ERROR',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, data, code, message = LoginService.admin_login(
            identifier=serializer.validated_data['identifier'],
            password=serializer.validated_data['password'],
            request=request,
        )

        if not success:
            return _error_response(code, message)

        return Response({
            'success': True,
            'code': code,
            'message': 'Admin login successful',
            'data': data,
        })


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Header: Authorization: Bearer <access_token>
    Body:   refresh  string  Refresh token to blacklist (required)

    Blacklists the refresh token so it can no longer be used to obtain
    new access tokens. Requires a valid access token in the header.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'code': 'VALIDATION_ERROR',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, code, message = LoginService.logout(
            refresh_token=serializer.validated_data['refresh'],
            user=request.user,
            request=request,
        )

        if not success:
            return _error_response(code, message)

        return Response({'success': True, 'code': code, 'message': 'Logout successful'})


class TokenRefreshView(APIView):
    """
    POST /api/v1/auth/token/refresh/

    Body:   refresh  string  Valid, non-blacklisted refresh token (required)

    Returns a new access token. The refresh token itself is NOT rotated here;
    rotation happens automatically via simplejwt when ROTATE_REFRESH_TOKENS=True.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'code': 'VALIDATION_ERROR',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, access_token, code, message = LoginService.refresh_access_token(
            refresh_token=serializer.validated_data['refresh'],
        )

        if not success:
            return _error_response(code, message)

        return Response({
            'success': True,
            'code': code,
            'data': {'access': access_token},
        })
