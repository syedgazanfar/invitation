"""
SMS Service using MSG91
"""
import os
import random
import requests
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache

from apps.accounts.models import PhoneVerification


class SMSService:
    """SMS Service for sending OTP and notifications"""
    
    MSG91_AUTH_KEY = os.getenv('MSG91_AUTH_KEY', '')
    MSG91_SENDER_ID = os.getenv('MSG91_SENDER_ID', 'INVITE')
    MSG91_ROUTE = os.getenv('MSG91_ROUTE', '4')  # 4 for transactional
    MSG91_TEMPLATE_ID = os.getenv('MSG91_TEMPLATE_ID', '')
    
    @classmethod
    def send_otp(cls, user, phone: str, otp: str) -> bool:
        """
        Send OTP via MSG91
        
        Args:
            user: User object
            phone: Phone number (with country code)
            otp: OTP code
            
        Returns:
            bool: True if sent successfully
        """
        if not cls.MSG91_AUTH_KEY:
            # Development mode - print to console
            print(f"\n{'='*50}")
            print(f"DEVELOPMENT MODE - OTP for {phone}: {otp}")
            print(f"{'='*50}\n")
            return True
        
        try:
            url = "https://api.msg91.com/api/v5/otp"
            
            payload = {
                "template_id": cls.MSG91_TEMPLATE_ID,
                "mobile": phone.replace('+', ''),  # Remove + for MSG91
                "authkey": cls.MSG91_AUTH_KEY,
                "otp": otp,
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('type') == 'success'
            else:
                print(f"MSG91 Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"SMS Error: {e}")
            return False
    
    @classmethod
    def send_sms(cls, phone: str, message: str) -> bool:
        """
        Send generic SMS
        
        Args:
            phone: Phone number
            message: Message text
            
        Returns:
            bool: True if sent successfully
        """
        if not cls.MSG91_AUTH_KEY:
            print(f"\nDEVELOPMENT SMS to {phone}: {message}\n")
            return True
        
        try:
            url = "https://api.msg91.com/api/v2/sendsms"
            
            payload = {
                "sender": cls.MSG91_SENDER_ID,
                "route": cls.MSG91_ROUTE,
                "country": "91",
                "sms": [{
                    "message": message,
                    "to": [phone.replace('+', '')]
                }]
            }
            
            headers = {
                'authkey': cls.MSG91_AUTH_KEY,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            print(f"SMS Error: {e}")
            return False
    
    @classmethod
    def generate_and_send_otp(cls, user, phone: str) -> tuple[bool, str]:
        """
        Generate OTP and send to user
        
        Returns:
            tuple: (success, otp)
        """
        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Save to database
        PhoneVerification.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address='127.0.0.1'  # Will be updated in view
        )
        
        # Send SMS
        success = cls.send_otp(user, phone, otp)
        
        return success, otp


class NotificationService:
    """Service for sending notifications"""
    
    @classmethod
    def send_order_approved_sms(cls, user, order):
        """Send SMS when order is approved"""
        message = (
            f"Dear {user.full_name or user.username}, "
            f"Your order {order.order_number} has been approved! "
            f"You can now create your invitation. "
            f"- InviteMe"
        )
        return SMSService.send_sms(user.phone, message)
    
    @classmethod
    def send_order_created_sms(cls, user, order):
        """Send SMS when order is created"""
        message = (
            f"Dear {user.full_name or user.username}, "
            f"Your order {order.order_number} of Rs.{order.payment_amount} has been received. "
            f"We'll notify you once approved. "
            f"- InviteMe"
        )
        return SMSService.send_sms(user.phone, message)
    
    @classmethod
    def send_invitation_created_sms(cls, user, invitation):
        """Send SMS when invitation is created"""
        message = (
            f"Your invitation '{invitation.event_title}' is ready! "
            f"Share it: {invitation.share_url} "
            f"- InviteMe"
        )
        return SMSService.send_sms(user.phone, message)
