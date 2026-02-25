"""
Public Views for Invitations (No authentication required)
These are accessed by guests who receive the invitation link
"""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Invitation, Guest
from .serializers import (
    PublicInvitationSerializer,
    GuestRegistrationSerializer,
    GuestCheckSerializer
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@api_view(['GET'])
@permission_classes([AllowAny])
def get_public_invitation(request, slug):
    """
    Get public invitation data
    This is called when someone opens the invitation link
    """
    try:
        invitation = Invitation.objects.select_related('template').get(
            slug=slug,
            is_active=True,
            is_expired=False
        )
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invitation not found or expired'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if link is still valid
    if invitation.link_expires_at and timezone.now() > invitation.link_expires_at:
        invitation.expire()
        return Response({
            'success': False,
            'message': 'This invitation link has expired'
        }, status=status.HTTP_410_GONE)
    
    # Increment view count
    invitation.increment_view()
    
    # Log the view
    from .models import InvitationViewLog
    InvitationViewLog.objects.create(
        invitation=invitation,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        referrer=request.META.get('HTTP_REFERER', '')
    )
    
    # Return public data
    serializer = PublicInvitationSerializer(invitation)
    
    return Response({
        'success': True,
        'data': {
            'invitation': serializer.data,
            'can_register': invitation.can_accept_guest(),
            'remaining_links': invitation.remaining_regular_links
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def check_guest_status(request, slug):
    """
    Check if this device has already registered as a guest
    Used before showing the registration form
    """
    try:
        invitation = Invitation.objects.get(
            slug=slug,
            is_active=True,
            is_expired=False
        )
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invitation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = GuestCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    fingerprint = serializer.validated_data['fingerprint']
    ip_address = get_client_ip(request)
    
    # Check for existing guest
    existing_guest = Guest.check_existing_guest(invitation.id, fingerprint, ip_address)
    
    if existing_guest:
        return Response({
            'success': True,
            'data': {
                'already_registered': True,
                'guest_name': existing_guest.name,
                'viewed_at': existing_guest.viewed_at,
                'message': f'Welcome back, {existing_guest.name}!'
            }
        })
    
    return Response({
        'success': True,
        'data': {
            'already_registered': False,
            'can_register': invitation.can_accept_guest(),
            'remaining_links': invitation.remaining_regular_links
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_guest(request, slug):
    """
    Register a new guest for the invitation
    This uses device fingerprinting to prevent duplicate registrations
    """
    try:
        invitation = Invitation.objects.get(
            slug=slug,
            is_active=True,
            is_expired=False
        )
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invitation not found or expired'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if link is still valid
    if invitation.link_expires_at and timezone.now() > invitation.link_expires_at:
        invitation.expire()
        return Response({
            'success': False,
            'message': 'This invitation link has expired'
        }, status=status.HTTP_410_GONE)
    
    serializer = GuestRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Generate fingerprint from provided data
    fingerprint = data.get('fingerprint')
    if not fingerprint:
        # Generate from available data
        fingerprint = Guest.generate_fingerprint(
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            screen_resolution=data.get('screen_resolution', ''),
            timezone_offset=data.get('timezone_offset', ''),
            languages=data.get('languages', ''),
            canvas_hash=data.get('canvas_hash', '')
        )
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check if this device already registered (extra safety check)
    existing = Guest.check_existing_guest(invitation.id, fingerprint, ip_address)
    if existing:
        return Response({
            'success': True,
            'message': f'Welcome back, {existing.name}!',
            'data': {
                'already_registered': True,
                'guest_name': existing.name,
                'total_guests': invitation.unique_guests
            }
        })
    
    # Check if invitation can accept more guests
    is_test = data.get('is_test', False)
    if not invitation.can_accept_guest(is_test):
        return Response({
            'success': False,
            'message': 'Sorry, this invitation has reached its guest limit'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Register the guest
    guest, created, message = Guest.register_guest(
        invitation=invitation,
        name=data['name'],
        phone=data.get('phone', ''),
        message=data.get('message', ''),
        fingerprint=fingerprint,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=data.get('session_id', ''),
        is_test=is_test
    )
    
    if guest is None:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': message,
        'data': {
            'already_registered': not created,
            'guest_name': guest.name,
            'total_guests': invitation.unique_guests,
            'remaining_links': invitation.remaining_test_links if is_test else invitation.remaining_regular_links
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def update_rsvp(request, slug):
    """
    Update RSVP status for an already registered guest
    """
    try:
        invitation = Invitation.objects.get(slug=slug, is_active=True)
    except Invitation.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invitation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    fingerprint = request.data.get('fingerprint')
    attending = request.data.get('attending')
    
    if fingerprint is None or attending is None:
        return Response({
            'success': False,
            'message': 'Fingerprint and attending status required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        guest = Guest.objects.get(
            invitation=invitation,
            device_fingerprint=fingerprint
        )
        guest.attending = attending
        guest.save(update_fields=['attending'])
        
        return Response({
            'success': True,
            'message': 'RSVP updated successfully',
            'data': {
                'attending': attending
            }
        })
    except Guest.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Guest not found'
        }, status=status.HTTP_404_NOT_FOUND)
