"""
Tests for Invitations App
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.plans.models import Plan, InvitationCategory, Template
from .models import Order, Invitation, Guest, OrderStatus

User = get_user_model()


class OrderAPITests(APITestCase):
    """Tests for Order API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            code='BASIC',
            name='Basic',
            regular_links=100,
            test_links=5,
            price_inr=150
        )
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_order(self):
        """Test creating an order"""
        url = reverse('order_create')
        data = {
            'plan_code': 'BASIC',
            'event_type': 'WEDDING',
            'event_type_name': 'Wedding',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(Order.objects.count(), 1)
    
    def test_list_orders(self):
        """Test listing user's orders"""
        Order.objects.create(
            user=self.user,
            plan=self.plan,
            event_type='WEDDING',
            event_type_name='Wedding',
            status=OrderStatus.PENDING_PAYMENT,
            payment_amount=150,
            granted_regular_links=100,
            granted_test_links=5
        )
        
        url = reverse('order_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_order_unauthenticated(self):
        """Test creating order without authentication"""
        self.client.force_authenticate(user=None)
        url = reverse('order_create')
        data = {
            'plan_code': 'BASIC',
            'event_type': 'WEDDING',
            'event_type_name': 'Wedding',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GuestTrackingTests(TestCase):
    """Tests for guest tracking and anti-fraud"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            code='BASIC',
            name='Basic',
            regular_links=100,
            test_links=5,
            price_inr=150
        )
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding'
        )
        self.template = Template.objects.create(
            plan=self.plan,
            category=self.category,
            name='Test Template',
            animation_type='elegant'
        )
        self.order = Order.objects.create(
            user=self.user,
            plan=self.plan,
            event_type='WEDDING',
            event_type_name='Wedding',
            status=OrderStatus.APPROVED,
            payment_amount=150,
            granted_regular_links=100,
            granted_test_links=5
        )
        self.invitation = Invitation.objects.create(
            order=self.order,
            user=self.user,
            template=self.template,
            event_title='Test Wedding',
            event_date=timezone.now() + timedelta(days=30),
            event_venue='Test Venue',
            host_name='Test Host',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=15)
        )
    
    def test_guest_registration(self):
        """Test guest registration"""
        guest, created, message = Guest.register_guest(
            invitation=self.invitation,
            name='Test Guest',
            phone='+919876543211',
            fingerprint='test_fingerprint_123',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            session_id='session123',
            is_test=False
        )
        
        self.assertIsNotNone(guest)
        self.assertTrue(created)
        self.assertEqual(Guest.objects.count(), 1)
        self.assertEqual(self.invitation.regular_links_used, 1)
    
    def test_duplicate_guest_prevention(self):
        """Test that same fingerprint cannot register twice"""
        # First registration
        Guest.register_guest(
            invitation=self.invitation,
            name='Test Guest',
            fingerprint='same_fingerprint',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            is_test=False
        )
        
        # Second registration with same fingerprint
        guest, created, message = Guest.register_guest(
            invitation=self.invitation,
            name='Different Name',
            fingerprint='same_fingerprint',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            is_test=False
        )
        
        self.assertFalse(created)
        self.assertEqual(Guest.objects.count(), 1)
        self.assertEqual(self.invitation.regular_links_used, 1)  # Should not increase
    
    def test_link_limit(self):
        """Test that link limit is enforced"""
        # Set link limit to 1
        self.order.granted_regular_links = 1
        self.order.save()
        
        # First guest registers
        Guest.register_guest(
            invitation=self.invitation,
            name='Guest 1',
            fingerprint='fp1',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            is_test=False
        )
        
        # Try to register second guest
        guest, created, message = Guest.register_guest(
            invitation=self.invitation,
            name='Guest 2',
            fingerprint='fp2',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            is_test=False
        )
        
        self.assertIsNone(guest)
        self.assertIn('limit', message.lower())


class InvitationExpiryTests(TestCase):
    """Tests for invitation expiry"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='testpass123'
        )
        self.plan = Plan.objects.create(
            code='BASIC',
            name='Basic',
            regular_links=100,
            test_links=5,
            price_inr=150
        )
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding'
        )
        self.template = Template.objects.create(
            plan=self.plan,
            category=self.category,
            name='Test Template',
            animation_type='elegant'
        )
        self.order = Order.objects.create(
            user=self.user,
            plan=self.plan,
            event_type='WEDDING',
            event_type_name='Wedding',
            status=OrderStatus.APPROVED,
            payment_amount=150,
            granted_regular_links=100,
            granted_test_links=5
        )
    
    def test_invitation_expires_after_15_days(self):
        """Test that invitation expires after 15 days"""
        invitation = Invitation.objects.create(
            order=self.order,
            user=self.user,
            template=self.template,
            event_title='Test Wedding',
            event_date=timezone.now() + timedelta(days=30),
            event_venue='Test Venue',
            host_name='Test Host',
            is_active=True,
            link_expires_at=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        self.assertFalse(invitation.is_link_valid)
    
    def test_invitation_not_expired(self):
        """Test that active invitation is valid"""
        invitation = Invitation.objects.create(
            order=self.order,
            user=self.user,
            template=self.template,
            event_title='Test Wedding',
            event_date=timezone.now() + timedelta(days=30),
            event_venue='Test Venue',
            host_name='Test Host',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=10)  # Expires in 10 days
        )
        
        self.assertTrue(invitation.is_link_valid)


class AdminAPITests(APITestCase):
    """Tests for Admin API"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            phone='+919876543210',
            username='admin',
            password='adminpass123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            phone='+919876543211',
            username='user',
            password='userpass123'
        )
        self.plan = Plan.objects.create(
            code='BASIC',
            name='Basic',
            regular_links=100,
            test_links=5,
            price_inr=150
        )
    
    def test_admin_dashboard_access(self):
        """Test admin dashboard access"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin_dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_dashboard_denied_for_regular_user(self):
        """Test that regular users cannot access admin dashboard"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('admin_dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_approve_order(self):
        """Test approving an order"""
        order = Order.objects.create(
            user=self.regular_user,
            plan=self.plan,
            event_type='WEDDING',
            event_type_name='Wedding',
            status=OrderStatus.PENDING_APPROVAL,
            payment_amount=150,
            granted_regular_links=100,
            granted_test_links=5
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin_approve_order', kwargs={'pk': order.id})
        
        response = self.client.post(url, {'notes': 'Approved by admin'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.APPROVED)
