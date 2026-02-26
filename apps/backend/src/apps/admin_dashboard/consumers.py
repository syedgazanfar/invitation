"""
WebSocket Consumers for Real-time Admin Dashboard Updates
"""
import json
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class AdminDashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time admin dashboard updates.
    
    This consumer handles:
    - Admin authentication via JWT token
    - Real-time approval status updates
    - Broadcast notifications to all connected admins
    - Keepalive/ping-pong for connection health
    """
    
    # Group name for all admin connections
    ADMIN_GROUP = 'admin_dashboard'
    
    async def connect(self):
        """
        Handle WebSocket connection.
        
        Authenticates the user and adds them to the admin group
        if they have admin privileges.
        """
        self.user = AnonymousUser()
        self.is_authenticated = False
        
        # Get token from query string
        query_string = self.scope.get('query_string', b'').decode()
        token = self._extract_token_from_query(query_string)
        
        # Authenticate user
        if token:
            user = await self._authenticate_user(token)
            if user and user.is_staff:
                self.user = user
                self.is_authenticated = True
        
        # Accept or reject connection
        if self.is_authenticated:
            await self.accept()
            # Add to admin group for broadcasts
            await self.channel_layer.group_add(
                self.ADMIN_GROUP,
                self.channel_name
            )
            
            # Send initial connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to admin dashboard',
                'user': await self._get_user_info()
            }))
            
            # Broadcast to other admins that a new admin joined
            await self.channel_layer.group_send(
                self.ADMIN_GROUP,
                {
                    'type': 'admin_joined',
                    'user_id': str(self.user.id),
                    'username': self.user.username
                }
            )
        else:
            await self.close(code=4001)  # Authentication failed
    
    async def disconnect(self, close_code: int):
        """
        Handle WebSocket disconnection.
        
        Removes the user from the admin group and notifies other admins.
        """
        if self.is_authenticated:
            # Remove from admin group
            await self.channel_layer.group_discard(
                self.ADMIN_GROUP,
                self.channel_name
            )
            
            # Notify other admins
            await self.channel_layer.group_send(
                self.ADMIN_GROUP,
                {
                    'type': 'admin_left',
                    'user_id': str(self.user.id),
                    'username': self.user.username
                }
            )
    
    async def receive(self, text_data: str):
        """
        Handle incoming WebSocket messages.
        
        Supports:
        - ping: Responds with pong for keepalive
        - get_stats: Returns current dashboard statistics
        - get_pending_count: Returns pending approvals count
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'get_stats':
                stats = await self._get_dashboard_stats()
                await self.send(text_data=json.dumps({
                    'type': 'stats_update',
                    'data': stats
                }))
            
            elif message_type == 'get_pending_count':
                count = await self._get_pending_count()
                await self.send(text_data=json.dumps({
                    'type': 'pending_count',
                    'count': count
                }))
            
            elif message_type == 'subscribe_approval_updates':
                # Client explicitly requests approval update subscription
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'channel': 'approval_updates'
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    # -------------------------------------------------------------------------
    # Event Handlers for Group Messages
    # -------------------------------------------------------------------------
    
    async def approval_update(self, event: Dict[str, Any]):
        """
        Handle approval status update broadcast.
        
        Sent when a user's approval status changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'approval_update',
            'action': event.get('action'),  # 'approved' or 'rejected'
            'user': event.get('user'),
            'performed_by': event.get('performed_by'),
            'timestamp': event.get('timestamp'),
            'notes': event.get('notes', '')
        }))
    
    async def pending_count_update(self, event: Dict[str, Any]):
        """
        Handle pending count update broadcast.
        
        Sent when the pending approvals count changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'pending_count_update',
            'count': event.get('count'),
            'change': event.get('change', 0)
        }))
    
    async def new_user_registered(self, event: Dict[str, Any]):
        """
        Handle new user registration broadcast.
        
        Sent when a new user registers and needs approval.
        """
        await self.send(text_data=json.dumps({
            'type': 'new_user',
            'user': event.get('user'),
            'timestamp': event.get('timestamp')
        }))
    
    async def admin_joined(self, event: Dict[str, Any]):
        """
        Handle admin joined notification.
        
        Sent when another admin connects to the dashboard.
        """
        # Don't send to the user who just joined
        if str(self.user.id) != event.get('user_id'):
            await self.send(text_data=json.dumps({
                'type': 'admin_joined',
                'user_id': event.get('user_id'),
                'username': event.get('username')
            }))
    
    async def admin_left(self, event: Dict[str, Any]):
        """
        Handle admin left notification.
        
        Sent when an admin disconnects from the dashboard.
        """
        await self.send(text_data=json.dumps({
            'type': 'admin_left',
            'user_id': event.get('user_id'),
            'username': event.get('username')
        }))
    
    async def order_status_update(self, event: Dict[str, Any]):
        """
        Handle order status update broadcast.
        
        Sent when an order status changes.
        """
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event.get('order_id'),
            'status': event.get('status'),
            'previous_status': event.get('previous_status'),
            'timestamp': event.get('timestamp')
        }))
    
    # -------------------------------------------------------------------------
    # Static Methods for Broadcasting
    # -------------------------------------------------------------------------
    
    @classmethod
    async def broadcast_approval_update(
        cls,
        user_data: Dict[str, Any],
        action: str,
        performed_by: Optional[Dict[str, Any]] = None,
        notes: str = ''
    ) -> None:
        """
        Broadcast an approval update to all connected admins.
        
        Args:
            user_data: Dictionary containing user information
            action: 'approved' or 'rejected'
            performed_by: Dictionary with admin user info who performed the action
            notes: Optional notes about the approval/rejection
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            cls.ADMIN_GROUP,
            {
                'type': 'approval_update',
                'action': action,
                'user': user_data,
                'performed_by': performed_by,
                'timestamp': json.dumps(str(__import__('datetime').datetime.now())),
                'notes': notes
            }
        )
    
    @classmethod
    async def broadcast_pending_count_update(
        cls,
        count: int,
        change: int = 0
    ) -> None:
        """
        Broadcast pending count update to all connected admins.
        
        Args:
            count: Current pending approvals count
            change: Change in count (+1 or -1)
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            cls.ADMIN_GROUP,
            {
                'type': 'pending_count_update',
                'count': count,
                'change': change
            }
        )
    
    @classmethod
    async def broadcast_new_user(cls, user_data: Dict[str, Any]) -> None:
        """
        Broadcast new user registration to all connected admins.
        
        Args:
            user_data: Dictionary containing new user information
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            cls.ADMIN_GROUP,
            {
                'type': 'new_user_registered',
                'user': user_data,
                'timestamp': json.dumps(str(__import__('datetime').datetime.now()))
            }
        )
    
    @classmethod
    async def broadcast_order_update(
        cls,
        order_id: str,
        status: str,
        previous_status: Optional[str] = None
    ) -> None:
        """
        Broadcast order status update to all connected admins.
        
        Args:
            order_id: UUID of the order
            status: New order status
            previous_status: Previous order status (optional)
        """
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            cls.ADMIN_GROUP,
            {
                'type': 'order_status_update',
                'order_id': order_id,
                'status': status,
                'previous_status': previous_status,
                'timestamp': json.dumps(str(__import__('datetime').datetime.now()))
            }
        )
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _extract_token_from_query(self, query_string: str) -> Optional[str]:
        """Extract JWT token from query string."""
        if not query_string:
            return None
        
        # Parse query string parameters
        params = {}
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
        
        return params.get('token')
    
    @database_sync_to_async
    def _authenticate_user(self, token: str):
        """Authenticate user using JWT token."""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            return User.objects.get(id=user_id)
        except (TokenError, User.DoesNotExist):
            return None
    
    @database_sync_to_async
    def _get_user_info(self) -> Dict[str, Any]:
        """Get user info for connection message."""
        return {
            'id': str(self.user.id),
            'username': self.user.username,
            'email': self.user.email,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser
        }
    
    @database_sync_to_async
    def _get_dashboard_stats(self) -> Dict[str, Any]:
        """Get current dashboard statistics."""
        from django.contrib.auth import get_user_model
        from apps.invitations.models import Order, Invitation
        from apps.admin_dashboard.models import AdminNotification
        from django.utils import timezone
        
        User = get_user_model()
        today = timezone.now().date()
        
        # Calculate total granted links
        total_granted_links = sum(
            order.granted_regular_links 
            for order in Order.objects.filter(status='APPROVED')
        )
        total_used_links = sum(
            order.used_links_count 
            for order in Order.objects.filter(status='APPROVED')
        )
        
        return {
            'total_users': User.objects.filter(is_staff=False).count(),
            'new_users_today': User.objects.filter(
                is_staff=False,
                created_at__date=today
            ).count(),
            'pending_approvals': User.objects.filter(
                is_staff=False,
                is_approved=False
            ).count(),
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(
                status__in=['PENDING_PAYMENT', 'PENDING_APPROVAL']
            ).count(),
            'approved_orders': Order.objects.filter(status='APPROVED').count(),
            'total_invitations': Invitation.objects.count(),
            'total_granted_links': total_granted_links,
            'total_used_links': total_used_links,
            'total_remaining_links': total_granted_links - total_used_links,
            'unread_notifications': AdminNotification.objects.filter(is_read=False).count(),
        }
    
    @database_sync_to_async
    def _get_pending_count(self) -> int:
        """Get current pending approvals count."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(is_staff=False, is_approved=False).count()
