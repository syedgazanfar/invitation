"""
Admin Dashboard Services - Notifications and Email
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import AdminNotification


class NotificationService:
    """Service for handling notifications and emails"""
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to newly registered user"""
        subject = f'Welcome to {settings.ADMIN_SETTINGS["COMPANY_NAME"]}!'
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #A61E2A;">Welcome to InviteMe!</h2>
                
                <p>Hello {user.full_name or user.username},</p>
                
                <p>Thank you for registering with InviteMe - India's premier digital invitation platform.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Your Account Details:</strong></p>
                    <p>Username: {user.username}</p>
                    <p>Phone: {user.phone}</p>
                </div>
                
                <p>Next Steps:</p>
                <ol>
                    <li>Choose a plan that suits your needs</li>
                    <li>Make the payment</li>
                    <li>Wait for admin approval (usually within 24 hours)</li>
                    <li>Start creating beautiful invitations!</li>
                </ol>
                
                <p>If you have any questions, feel free to contact us at {settings.ADMIN_SETTINGS['SUPPORT_EMAIL']}</p>
                
                <p>Best regards,<br>Team InviteMe</p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                html_message=html_message,
                fail_silently=True
            )
            return True
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False
    
    @staticmethod
    def notify_admin_new_user(user):
        """Create notification for admin when new user registers"""
        # Create in-app notification
        notification = AdminNotification.objects.create(
            notification_type=AdminNotification.NotificationType.NEW_USER,
            title=f'New User: {user.username}',
            message=f'{user.full_name or user.username} has registered with phone {user.phone}. Please review and approve.',
            user=user,
            metadata={
                'username': user.username,
                'phone': user.phone,
                'email': user.email,
                'full_name': user.full_name,
                'registered_at': user.created_at.isoformat() if hasattr(user, 'created_at') else None
            }
        )
        
        # Send email to admin
        subject = f'[InviteMe] New User Registration: {user.username}'
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #A61E2A;">New User Registration</h2>
                
                <p>A new user has registered on the platform.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>User Details:</strong></p>
                    <table style="width: 100%;">
                        <tr><td><strong>Username:</strong></td><td>{user.username}</td></tr>
                        <tr><td><strong>Full Name:</strong></td><td>{user.full_name or 'N/A'}</td></tr>
                        <tr><td><strong>Phone:</strong></td><td>{user.phone}</td></tr>
                        <tr><td><strong>Email:</strong></td><td>{user.email or 'N/A'}</td></tr>
                        <tr><td><strong>Registered:</strong></td><td>{user.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(user, 'created_at') else 'N/A'}</td></tr>
                    </table>
                </div>
                
                <p style="background: #fff3cd; padding: 10px; border-radius: 5px;">
                    <strong>Action Required:</strong> Please contact the user to verify details and approve their account after payment.
                </p>
                
                <p>
                    <a href="http://localhost/admin-dashboard/" 
                       style="background: #A61E2A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                       View in Admin Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send admin notification email: {e}")
        
        return notification
    
    @staticmethod
    def notify_user_approved(user, approved_by=None):
        """Send email to user when their account is approved"""
        subject = 'Your InviteMe Account Has Been Approved!'
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">🎉 Congratulations!</h2>
                
                <p>Hello {user.full_name or user.username},</p>
                
                <p>Your InviteMe account has been <strong>approved</strong>! You can now start creating beautiful digital invitations.</p>
                
                <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Your Current Plan:</strong> {user.current_plan.name if user.current_plan else 'Not Selected'}</p>
                    <p>You can now access all templates included in your plan.</p>
                </div>
                
                <p>
                    <a href="http://localhost/templates.html" 
                       style="background: #A61E2A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                       Browse Templates
                    </a>
                </p>
                
                <p>Thank you for choosing InviteMe!</p>
                
                <p>Best regards,<br>Team InviteMe</p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else [],
                html_message=html_message,
                fail_silently=True
            )
            return True
        except Exception as e:
            print(f"Failed to send approval email: {e}")
            return False
    
    @staticmethod
    def notify_plan_change_request(user, requested_plan):
        """Notify admin about plan change request"""
        notification = AdminNotification.objects.create(
            notification_type=AdminNotification.NotificationType.PLAN_CHANGE_REQUEST,
            title=f'Plan Change Request: {user.username}',
            message=f'{user.username} wants to change to {requested_plan.name} plan.',
            user=user,
            metadata={
                'username': user.username,
                'current_plan': user.current_plan.code if user.current_plan else None,
                'requested_plan': requested_plan.code,
                'requested_at': user.plan_change_requested_at.isoformat() if user.plan_change_requested_at else None
            }
        )
        return notification
    
    @staticmethod
    def get_unread_notifications():
        """Get all unread admin notifications"""
        return AdminNotification.objects.filter(is_read=False)
    
    @staticmethod
    def mark_notification_read(notification_id):
        """Mark a notification as read"""
        from django.utils import timezone
        try:
            notification = AdminNotification.objects.get(id=notification_id)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return True
        except AdminNotification.DoesNotExist:
            return False
