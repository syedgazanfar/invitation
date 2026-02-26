"""
Views for Orders and Invitations
"""
import csv
from io import StringIO
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, Invitation, Guest, InvitationViewLog
from .serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    InvitationListSerializer,
    InvitationDetailSerializer,
    InvitationCreateSerializer,
    InvitationUpdateSerializer,
    GuestSerializer,
    InvitationStatsSerializer
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ==================== ORDER VIEWS ====================

class OrderListView(generics.ListAPIView):
    """List user's orders"""
    serializer_class = OrderListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).select_related('plan').prefetch_related('invitation')


class OrderDetailView(generics.RetrieveAPIView):
    """Get order details"""
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).select_related('plan', 'approved_by')


class OrderCreateView(generics.CreateAPIView):
    """Create new order - users are locked to their current plan"""
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        user = request.user
        plan_code = request.data.get('plan_code', '').upper()
        
        # Check if user has a current plan locked
        if user.current_plan:
            # User can only reorder their current plan
            if plan_code != user.current_plan.code:
                return Response({
                    'success': False,
                    'message': f'You are subscribed to the {user.current_plan.name} plan. To change plans, please contact admin support.',
                    'data': {
                        'current_plan': {
                            'code': user.current_plan.code,
                            'name': user.current_plan.name
                        },
                        'can_change_plan': not user.plan_change_requested,
                        'plan_change_requested': user.plan_change_requested
                    }
                }, status=status.HTTP_403_FORBIDDEN)
        
        # User doesn't have a plan yet - allow first purchase
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Set user's current plan on first order
        if not user.current_plan:
            user.current_plan = order.plan
            user.save(update_fields=['current_plan'])
        
        return Response({
            'success': True,
            'message': 'Order created successfully',
            'data': OrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)


# ==================== INVITATION VIEWS ====================

class InvitationListView(generics.ListAPIView):
    """List user's invitations"""
    serializer_class = InvitationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Invitation.objects.filter(
            user=self.request.user
        ).select_related('template', 'order')


class InvitationDetailView(generics.RetrieveAPIView):
    """Get invitation details"""
    serializer_class = InvitationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Invitation.objects.filter(
            user=self.request.user
        ).select_related('template', 'order').prefetch_related('guests')


class InvitationCreateView(generics.CreateAPIView):
    """Create invitation for an order"""
    serializer_class = InvitationCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Invitation created successfully',
            'data': InvitationDetailSerializer(invitation).data
        }, status=status.HTTP_201_CREATED)


class InvitationUpdateView(generics.UpdateAPIView):
    """Update invitation"""
    serializer_class = InvitationUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Invitation.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if invitation can be edited
        if instance.is_expired:
            return Response({
                'success': False,
                'message': 'Cannot edit expired invitation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Invitation updated successfully',
            'data': InvitationDetailSerializer(instance).data
        })


class InvitationStatsView(APIView):
    """Get invitation statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, slug):
        try:
            invitation = Invitation.objects.get(slug=slug, user=request.user)
        except Invitation.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invitation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from django.utils import timezone
        expires_in_days = 0
        if invitation.link_expires_at:
            expires_in_days = max(0, (invitation.link_expires_at - timezone.now()).days)
        
        stats = {
            'total_views': invitation.total_views,
            'unique_guests': invitation.unique_guests,
            'regular_links_used': invitation.regular_links_used,
            'test_links_used': invitation.test_links_used,
            'remaining_regular_links': invitation.remaining_regular_links,
            'remaining_test_links': invitation.remaining_test_links,
            'is_link_valid': invitation.is_link_valid,
            'expires_in_days': expires_in_days
        }
        
        return Response({
            'success': True,
            'data': stats
        })


class GuestListView(generics.ListAPIView):
    """List guests for an invitation"""
    serializer_class = GuestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return Guest.objects.filter(
            invitation__slug=slug,
            invitation__user=self.request.user
        )


class ExportGuestsView(APIView):
    """Export guests to CSV"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, slug):
        try:
            invitation = Invitation.objects.get(slug=slug, user=request.user)
        except Invitation.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invitation not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        guests = Guest.objects.filter(invitation=invitation)
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Name', 'Phone', 'Message', 'Attending',
            'Device Type', 'Browser', 'OS', 'Viewed At', 'Is Test Link'
        ])
        
        # Data
        for guest in guests:
            writer.writerow([
                guest.name,
                guest.phone or 'N/A',
                guest.message or 'N/A',
                'Yes' if guest.attending else 'No' if guest.attending is False else 'N/A',
                guest.device_type,
                guest.browser,
                guest.os,
                guest.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if guest.is_test_link else 'No'
            ])
        
        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="guests_{slug}.csv"'
        
        return response
