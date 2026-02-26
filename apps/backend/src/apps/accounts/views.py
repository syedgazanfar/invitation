"""
Views for User Accounts
"""
import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    OTPSerializer,
    PhoneOnlySerializer,
    TokenResponseSerializer
)
from .models import PhoneVerification, UserActivityLog
from utils.sms_service import SMSService

# Import admin notification service
try:
    from apps.admin_dashboard.services import NotificationService
except ImportError:
    NotificationService = None

User = get_user_model()


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, activity_type, description='', request=None, metadata=None):
    """Log user activity"""
    try:
        UserActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            metadata=metadata or {}
        )
    except Exception:
        pass  # Don't let logging failures break the app


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Get IP address
        ip_address = get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            user.signup_ip = ip_address
            user.save()
            
            # Send welcome email to user
            if NotificationService:
                NotificationService.send_welcome_email(user)
                
                # Notify admin about new registration
                NotificationService.notify_admin_new_user(user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Log activity
            log_activity(user, 'LOGIN', 'User registered and logged in', request)
            
            return Response({
                'success': True,
                'message': 'User registered successfully. Please wait for admin approval before creating invitations.',
                'data': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': str(user.id),
                        'phone': user.phone,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name,
                        'is_phone_verified': user.is_phone_verified,
                        'is_approved': user.is_approved
                    }
                }
            }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login view"""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Try to find user by username or phone
        try:
            # First try username
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Then try phone number
            try:
                # Normalize phone if it looks like one
                phone = username.replace(' ', '').replace('-', '')
                if not phone.startswith('+91'):
                    phone = '+91' + phone[-10:]
                user = User.objects.get(phone=phone)
            except (User.DoesNotExist, IndexError):
                return Response({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is blocked
        if user.is_blocked:
            return Response({
                'success': False,
                'message': 'Your account has been blocked. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Select related data to avoid N+1 queries
        user = User.objects.select_related('current_plan').get(id=user.id)

        # Check password
        if not user.check_password(password):
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Check if user is approved (skip for superusers)
        if not user.is_approved and not user.is_superuser:
            return Response({
                'success': False,
                'message': 'Your account is pending admin approval. Please wait for verification or contact support.',
                'data': {
                    'approval_status': 'PENDING',
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'is_approved': user.is_approved
                    }
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last login IP
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login_ip'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Log activity
        log_activity(user, 'LOGIN', 'User logged in', request)
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': str(user.id),
                    'phone': user.phone,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_phone_verified': user.is_phone_verified,
                    'is_approved': user.is_approved,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'current_plan': {
                        'code': user.current_plan.code,
                        'name': user.current_plan.name
                    } if user.current_plan else None
                }
            }
        })


class LogoutView(generics.GenericAPIView):
    """User logout view - blacklists the refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log activity
            log_activity(request.user, 'LOGOUT', 'User logged out', request)
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Log activity
        log_activity(request.user, 'PROFILE_UPDATE', 'Profile updated', request)
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': serializer.data
        })


class PasswordChangeView(generics.GenericAPIView):
    """Change password view"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log activity
        log_activity(user, 'PASSWORD_CHANGE', 'Password changed', request)
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })


class SendOTPView(generics.GenericAPIView):
    """Send OTP to phone number"""
    serializer_class = PhoneOnlySerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        
        # Normalize phone
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('+91'):
            phone = '+91' + phone[-10:]
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate and send OTP
        success, otp = SMSService.generate_and_send_otp(user, phone)
        
        # Update IP address
        PhoneVerification.objects.filter(
            user=user,
            otp=otp,
            is_used=False
        ).update(ip_address=get_client_ip(request))
        
        if success:
            return Response({
                'success': True,
                'message': 'OTP sent successfully',
                'data': {
                    'otp': otp if not SMSService.MSG91_AUTH_KEY else None,
                    'expires_in_minutes': 10
                }
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(generics.GenericAPIView):
    """Verify OTP and mark phone as verified"""
    serializer_class = OTPSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']
        
        # Normalize phone
        phone = phone.replace(' ', '').replace('-', '')
        if not phone.startswith('+91'):
            phone = '+91' + phone[-10:]
        
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get latest unused OTP
        try:
            verification = PhoneVerification.objects.filter(
                user=user,
                otp=otp,
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')
        except PhoneVerification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid or expired OTP'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as used and verify phone
        verification.is_used = True
        verification.save()
        
        user.is_phone_verified = True
        user.phone_verified_at = timezone.now()
        user.save()
        
        return Response({
            'success': True,
            'message': 'Phone number verified successfully'
        })


class MyPlanView(generics.GenericAPIView):
    """Get user's current plan details"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get latest approved order to determine current plan
        latest_order = user.orders.filter(
            status='APPROVED'
        ).select_related('plan').first()
        
        if latest_order and latest_order.plan:
            # Update user's current plan if not set
            if not user.current_plan:
                user.current_plan = latest_order.plan
                user.save(update_fields=['current_plan'])
            
            plan_data = {
                'code': latest_order.plan.code,
                'name': latest_order.plan.name,
                'price': latest_order.plan.price,
                'link_limit': latest_order.plan.link_limit,
                'test_links': latest_order.plan.test_links,
            }
        else:
            plan_data = None
        
        return Response({
            'success': True,
            'data': {
                'current_plan': plan_data,
                'plan_change_requested': user.plan_change_requested,
                'plan_change_requested_at': user.plan_change_requested_at,
                'can_change_plan': not user.plan_change_requested
            }
        })


class RequestPlanChangeView(generics.GenericAPIView):
    """Request a plan change - requires admin approval"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Select related data to avoid N+1 queries
        user = User.objects.select_related('current_plan').get(id=request.user.id)

        # Check if user already has a pending request
        if user.plan_change_requested:
            return Response({
                'success': False,
                'message': 'You already have a pending plan change request. Please wait for admin approval or contact support.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get requested plan
        plan_code = request.data.get('plan_code')
        if not plan_code:
            return Response({
                'success': False,
                'message': 'Please specify the plan you want to change to'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.plans.models import Plan
            new_plan = Plan.objects.get(code=plan_code.upper(), is_active=True)
        except Plan.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid plan selected'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user already has this plan
        if user.current_plan and user.current_plan.code == new_plan.code:
            return Response({
                'success': False,
                'message': 'You are already subscribed to this plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create plan change request
        user.request_plan_change()
        
        # Log activity
        log_activity(
            user, 
            'PLAN_CHANGE_REQUEST', 
            f'Requested plan change to {new_plan.name}',
            request,
            {'requested_plan': new_plan.code, 'current_plan': user.current_plan.code if user.current_plan else None}
        )
        
        return Response({
            'success': True,
            'message': 'Plan change request submitted successfully. An admin will review your request and contact you.',
            'data': {
                'requested_plan': {
                    'code': new_plan.code,
                    'name': new_plan.name,
                    'price': new_plan.price
                },
                'status': 'PENDING_ADMIN_APPROVAL'
            }
        })
