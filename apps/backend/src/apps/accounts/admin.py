"""
Admin configuration for accounts app

This module provides a comprehensive admin interface for User management,
including plan approval workflows, real-time status updates, and audit logging.
"""
from typing import Optional, Any
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.db.models import QuerySet
from django import forms

from .models import User, PhoneVerification, UserActivityLog


class UserApprovalForm(forms.Form):
    """Form for approving a user with notes."""
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        required=False,
        help_text="Optional notes about the approval"
    )
    payment_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Payment amount received"
    )
    payment_method = forms.ChoiceField(
        choices=[
            ('', '--- Select ---'),
            ('UPI', 'UPI'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CASH', 'Cash'),
            ('RAZORPAY', 'Razorpay'),
        ],
        required=False
    )


class UserRejectionForm(forms.Form):
    """Form for rejecting a user with reason."""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        required=True,
        help_text="Reason for rejection (will be recorded)"
    )
    block_user = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Block user after rejection"
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin with plan approval workflow.
    
    This admin interface provides:
    - Visual status indicators for approval and payment status
    - Quick approve/reject actions in the list view
    - Detailed plan information display
    - Audit logging of all approval actions
    """
    
    # List view columns - customized to show approval workflow
    list_display = [
        'phone', 'username', 'full_name', 'email',
        'current_plan_display', 'approval_status_display', 
        'payment_status_display', 'created_at', 'approval_actions'
    ]
    
    # Filters for the list view
    list_filter = [
        'is_approved', 'payment_verified', 'current_plan__code',
        'plan_change_requested', 'is_active', 'is_blocked', 
        'is_staff', 'created_at', 'is_phone_verified'
    ]
    
    # Search fields
    search_fields = [
        'phone', 'username', 'email', 'full_name', 'notes'
    ]
    
    # Ordering
    ordering = ['-created_at']
    
    # Fieldsets for detail view - organized by functionality
    fieldsets = (
        ('User Information', {
            'fields': (
                'phone', 'username', 'full_name', 'email', 'password'
            ),
            'classes': ('wide',)
        }),
        ('Plan Information', {
            'fields': (
                'current_plan', 'plan_change_requested',
                'plan_change_requested_at', 'view_plan_details'
            ),
            'classes': ('wide', 'collapse'),
            'description': 'User\'s subscription plan details'
        }),
        ('Approval Status', {
            'fields': (
                'is_approved', 'approved_at', 'approved_by',
                'payment_verified', 'notes', 'view_approval_history'
            ),
            'classes': ('wide',),
            'description': 'Admin approval and payment verification status'
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_blocked', 'is_staff', 
                'is_superuser', 'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': (
                'is_phone_verified', 'phone_verified_at'
            ),
            'classes': ('collapse',)
        }),
        ('IP Information', {
            'fields': ('signup_ip', 'last_login_ip'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = [
        'approved_at', 'approved_by', 'plan_change_requested_at',
        'view_plan_details', 'view_approval_history',
        'created_at', 'updated_at', 'phone_verified_at',
        'last_login', 'date_joined'
    ]
    
    # Add fieldsets
    add_fieldsets = [
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone', 'username', 'email', 'full_name', 
                'password1', 'password2'
            ),
        }),
    ]
    
    # Actions
    actions = [
        'approve_users', 'reject_users', 'block_users', 
        'unblock_users', 'verify_payment', 'reset_plan_change_request'
    ]
    
    # Custom URLs for approval actions
    def get_urls(self):
        """Add custom URLs for approval/rejection actions."""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<uuid:user_id>/approve/',
                self.admin_site.admin_view(self.approve_user_view),
                name='accounts_user_approve'
            ),
            path(
                '<uuid:user_id>/reject/',
                self.admin_site.admin_view(self.reject_user_view),
                name='accounts_user_reject'
            ),
        ]
        return custom_urls + urls
    
    # -------------------------------------------------------------------------
    # Custom Display Methods
    # -------------------------------------------------------------------------
    
    def current_plan_display(self, obj: User) -> str:
        """
        Display current plan with color-coded badge.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with plan badge
        """
        if not obj.current_plan:
            return format_html(
                '<span style="color: #999;">No Plan</span>'
            )
        
        # Color coding by plan tier
        plan_colors = {
            'BASIC': '#28a745',    # Green
            'PREMIUM': '#007bff',  # Blue
            'LUXURY': '#6f42c1'    # Purple
        }
        
        color = plan_colors.get(obj.current_plan.code, '#6c757d')
        
        # Show plan change indicator
        change_indicator = ''
        if obj.plan_change_requested:
            change_indicator = format_html(
                ' <span style="color: #fd7e14; font-size: 11px;">'
                '(Change Requested)</span>'
            )
        
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>{}',
            color, obj.current_plan.name, change_indicator
        )
    current_plan_display.short_description = 'Current Plan'
    current_plan_display.admin_order_field = 'current_plan__code'
    
    def approval_status_display(self, obj: User) -> str:
        """
        Display approval status with color badge.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with status badge
        """
        if obj.is_approved:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">'
                '✓ Approved</span>'
            )
        else:
            return format_html(
                '<span style="background: #ffc107; color: #000; padding: 2px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: 600;">'
                '⏳ Pending</span>'
            )
    approval_status_display.short_description = 'Approval Status'
    approval_status_display.admin_order_field = 'is_approved'
    
    def payment_status_display(self, obj: User) -> str:
        """
        Display payment verification status.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with payment status
        """
        if obj.payment_verified:
            return format_html(
                '<span style="color: #28a745;">✓ Verified</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ Not Verified</span>'
            )
    payment_status_display.short_description = 'Payment'
    payment_status_display.admin_order_field = 'payment_verified'
    
    def approval_actions(self, obj: User) -> str:
        """
        Display approve/reject action buttons in list view.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with action buttons
        """
        if obj.is_approved:
            return format_html(
                '<span style="color: #28a745;">Approved</span>'
            )
        
        # Generate URLs for actions
        approve_url = reverse('admin:accounts_user_approve', args=[obj.id])
        reject_url = reverse('admin:accounts_user_reject', args=[obj.id])
        
        return format_html(
            '<a href="{}" style="background: #28a745; color: white; padding: 4px 10px; '
            'border-radius: 4px; text-decoration: none; margin-right: 5px; font-size: 12px;">'
            'Approve</a>'
            '<a href="{}" style="background: #dc3545; color: white; padding: 4px 10px; '
            'border-radius: 4px; text-decoration: none; font-size: 12px;">'
            'Reject</a>',
            approve_url, reject_url
        )
    approval_actions.short_description = 'Actions'
    
    def view_plan_details(self, obj: User) -> str:
        """
        Display detailed plan information in the admin detail view.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with plan details
        """
        if not obj.current_plan:
            return 'No plan selected'
        
        plan = obj.current_plan
        features_list = '<ul style="margin: 0; padding-left: 20px;">'
        for feature in plan.features[:5]:  # Show first 5 features
            features_list += f'<li>{feature}</li>'
        features_list += '</ul>'
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;">'
            '<h4 style="margin-top: 0;">{} Plan Details</h4>'
            '<table style="width: 100%;">'
            '<tr><td><strong>Price:</strong></td><td>₹{}</td></tr>'
            '<tr><td><strong>Regular Links:</strong></td><td>{}</td></tr>'
            '<tr><td><strong>Test Links:</strong></td><td>{}</td></tr>'
            '<tr><td><strong>Features:</strong></td><td>{}</td></tr>'
            '</table></div>',
            plan.name,
            plan.price_inr,
            plan.regular_links,
            plan.test_links,
            mark_safe(features_list)
        )
    view_plan_details.short_description = 'Plan Details'
    
    def view_approval_history(self, obj: User) -> str:
        """
        Display approval history for the user.
        
        Args:
            obj: User instance
            
        Returns:
            HTML string with approval history
        """
        from apps.admin_dashboard.models import UserApprovalLog
        
        logs = UserApprovalLog.objects.filter(user=obj).order_by('-created_at')[:10]
        
        if not logs:
            return '<p>No approval history</p>'
        
        html = '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px;">'
        html += '<h4 style="margin-top: 0;">Approval History</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<thead><tr style="border-bottom: 2px solid #dee2e6;">'
        html += '<th style="text-align: left; padding: 8px;">Date</th>'
        html += '<th style="text-align: left; padding: 8px;">Action</th>'
        html += '<th style="text-align: left; padding: 8px;">By</th>'
        html += '<th style="text-align: left; padding: 8px;">Notes</th>'
        html += '</tr></thead><tbody>'
        
        for log in logs:
            action_color = '#28a745' if log.action == 'APPROVED' else '#dc3545' if log.action == 'REJECTED' else '#6c757d'
            html += f'<tr style="border-bottom: 1px solid #dee2e6;">'
            html += f'<td style="padding: 8px;">{log.created_at.strftime("%Y-%m-%d %H:%M")}</td>'
            html += f'<td style="padding: 8px; color: {action_color}; font-weight: 600;">{log.action}</td>'
            html += f'<td style="padding: 8px;">{log.approved_by.username if log.approved_by else "System"}</td>'
            html += f'<td style="padding: 8px;">{log.notes or "-"}</td>'
            html += '</tr>'
        
        html += '</tbody></table></div>'
        
        return mark_safe(html)
    view_approval_history.short_description = 'Approval History'
    
    # -------------------------------------------------------------------------
    # Custom Admin Views
    # -------------------------------------------------------------------------
    
    def approve_user_view(self, request, user_id: str):
        """
        Custom view for approving a user.
        
        Args:
            request: HTTP request
            user_id: UUID of the user to approve
            
        Returns:
            HttpResponseRedirect to user changelist
        """
        from apps.admin_dashboard.models import UserApprovalLog
        from apps.admin_dashboard.services import NotificationService
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.message_user(request, 'User not found', messages.ERROR)
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        
        if user.is_approved:
            self.message_user(request, 'User is already approved', messages.WARNING)
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        
        if request.method == 'POST':
            form = UserApprovalForm(request.POST)
            if form.is_valid():
                # Approve user
                user.is_approved = True
                user.approved_at = timezone.now()
                user.approved_by = request.user
                user.payment_verified = True
                
                notes = form.cleaned_data.get('notes', '')
                if notes:
                    user.notes = notes
                
                user.save()
                
                # Create approval log
                UserApprovalLog.objects.create(
                    user=user,
                    approved_by=request.user,
                    action='APPROVED',
                    notes=notes,
                    payment_method=form.cleaned_data.get('payment_method', ''),
                    payment_amount=form.cleaned_data.get('payment_amount')
                )
                
                # Send notification
                try:
                    NotificationService.notify_user_approved(user, request.user)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send approval notification: {e}")
                
                self.message_user(
                    request, 
                    f'User "{user.username}" has been approved successfully.',
                    messages.SUCCESS
                )
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        else:
            form = UserApprovalForm()
        
        # Render approval form
        from django.template.response import TemplateResponse
        context = {
            'form': form,
            'user': user,
            'title': f'Approve User: {user.username}',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/accounts/user_approve_form.html', context)
    
    def reject_user_view(self, request, user_id: str):
        """
        Custom view for rejecting a user.
        
        Args:
            request: HTTP request
            user_id: UUID of the user to reject
            
        Returns:
            HttpResponseRedirect to user changelist
        """
        from apps.admin_dashboard.models import UserApprovalLog
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.message_user(request, 'User not found', messages.ERROR)
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        
        if request.method == 'POST':
            form = UserRejectionForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data['reason']
                block_user = form.cleaned_data['block_user']
                
                # Create rejection log
                UserApprovalLog.objects.create(
                    user=user,
                    approved_by=request.user,
                    action='REJECTED',
                    notes=reason
                )
                
                # Optionally block user
                if block_user:
                    user.is_blocked = True
                    user.block_reason = reason
                    user.save()
                
                self.message_user(
                    request,
                    f'User "{user.username}" has been rejected.',
                    messages.SUCCESS
                )
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
        else:
            form = UserRejectionForm()
        
        # Render rejection form
        from django.template.response import TemplateResponse
        context = {
            'form': form,
            'user': user,
            'title': f'Reject User: {user.username}',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/accounts/user_reject_form.html', context)
    
    # -------------------------------------------------------------------------
    # Admin Actions
    # -------------------------------------------------------------------------
    
    def approve_users(self, request, queryset: QuerySet):
        """
        Bulk action to approve multiple users.
        
        Args:
            request: HTTP request
            queryset: QuerySet of users to approve
        """
        from apps.admin_dashboard.models import UserApprovalLog
        
        approved_count = 0
        for user in queryset.filter(is_approved=False):
            user.is_approved = True
            user.approved_at = timezone.now()
            user.approved_by = request.user
            user.payment_verified = True
            user.save()
            
            UserApprovalLog.objects.create(
                user=user,
                approved_by=request.user,
                action='APPROVED',
                notes='Bulk approval'
            )
            approved_count += 1
        
        self.message_user(
            request,
            f'{approved_count} user(s) approved successfully.',
            messages.SUCCESS
        )
    approve_users.short_description = 'Approve selected users'
    
    def reject_users(self, request, queryset: QuerySet):
        """
        Bulk action to reject multiple users.
        
        Args:
            request: HTTP request
            queryset: QuerySet of users to reject
        """
        from apps.admin_dashboard.models import UserApprovalLog
        
        rejected_count = 0
        for user in queryset.filter(is_approved=False):
            UserApprovalLog.objects.create(
                user=user,
                approved_by=request.user,
                action='REJECTED',
                notes='Bulk rejection'
            )
            user.is_blocked = True
            user.block_reason = 'Bulk rejection by admin'
            user.save()
            rejected_count += 1
        
        self.message_user(
            request,
            f'{rejected_count} user(s) rejected and blocked.',
            messages.SUCCESS
        )
    reject_users.short_description = 'Reject selected users'
    
    def block_users(self, request, queryset: QuerySet):
        """Block selected users."""
        queryset.update(is_blocked=True, blocked_at=timezone.now())
        self.message_user(
            request,
            f'{queryset.count()} user(s) blocked.',
            messages.SUCCESS
        )
    block_users.short_description = 'Block selected users'
    
    def unblock_users(self, request, queryset: QuerySet):
        """Unblock selected users."""
        queryset.update(is_blocked=False, blocked_at=None)
        self.message_user(
            request,
            f'{queryset.count()} user(s) unblocked.',
            messages.SUCCESS
        )
    unblock_users.short_description = 'Unblock selected users'
    
    def verify_payment(self, request, queryset: QuerySet):
        """Mark payment as verified for selected users."""
        queryset.update(payment_verified=True)
        self.message_user(
            request,
            f'Payment verified for {queryset.count()} user(s).',
            messages.SUCCESS
        )
    verify_payment.short_description = 'Verify payment for selected users'
    
    def reset_plan_change_request(self, request, queryset: QuerySet):
        """Reset plan change request flag."""
        queryset.update(
            plan_change_requested=False,
            plan_change_requested_at=None
        )
        self.message_user(
            request,
            f'Plan change request reset for {queryset.count()} user(s).',
            messages.SUCCESS
        )
    reset_plan_change_request.short_description = 'Reset plan change request'


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    """Admin for phone verification records."""
    list_display = ['user', 'otp_masked', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__phone', 'otp']
    readonly_fields = ['created_at']
    
    def otp_masked(self, obj: PhoneVerification) -> str:
        """Display masked OTP for security."""
        if len(obj.otp) > 2:
            return obj.otp[:2] + '*' * (len(obj.otp) - 2)
        return '***'
    otp_masked.short_description = 'OTP'


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin for user activity logs."""
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__phone', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
