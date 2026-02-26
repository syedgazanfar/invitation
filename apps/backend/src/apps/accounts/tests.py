"""
Tests for Accounts App
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """Tests for user registration"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
    
    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            'phone': '+919876543210',
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().phone, '+919876543210')
    
    def test_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = {
            'phone': '+919876543210',
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'differentpass',
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(phone='+919876543210').exists())
    
    def test_registration_duplicate_phone(self):
        """Test registration with duplicate phone number"""
        User.objects.create_user(
            phone='+919876543210',
            username='existing',
            password='testpass123'
        )
        
        data = {
            'phone': '+919876543210',
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTests(APITestCase):
    """Tests for user login"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='testpass123'
        )
    
    def test_successful_login(self):
        """Test successful login"""
        data = {
            'phone': '+919876543210',
            'password': 'testpass123',
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'phone': '+919876543210',
            'password': 'wrongpassword',
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_blocked_user(self):
        """Test login with blocked user"""
        self.user.is_blocked = True
        self.user.save()
        
        data = {
            'phone': '+919876543210',
            'password': 'testpass123',
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserProfileTests(APITestCase):
    """Tests for user profile"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='testpass123'
        )
        self.profile_url = reverse('profile')
    
    def test_get_profile_authenticated(self):
        """Test getting profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['phone'], '+919876543210')
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile when not authenticated"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile(self):
        """Test updating profile"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'full_name': 'Updated Name',
            'email': 'updated@example.com',
        }
        
        response = self.client.put(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')


class PasswordChangeTests(APITestCase):
    """Tests for password change"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='+919876543210',
            username='testuser',
            password='oldpass123'
        )
        self.change_password_url = reverse('change_password')
        self.client.force_authenticate(user=self.user)
    
    def test_successful_password_change(self):
        """Test successful password change"""
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
