"""
URL configuration for invitations app (authenticated routes)
"""
from django.urls import path
from . import views
from .payment_views import (
    CreateRazorpayOrderView,
    RazorpayWebhookView,
    VerifyRazorpayPaymentView
)

urlpatterns = [
    # Orders
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Invitations
    path('', views.InvitationListView.as_view(), name='invitation_list'),
    path('create/', views.InvitationCreateView.as_view(), name='invitation_create'),
    path('<slug:slug>/', views.InvitationDetailView.as_view(), name='invitation_detail'),
    path('<slug:slug>/update/', views.InvitationUpdateView.as_view(), name='invitation_update'),
    path('<slug:slug>/stats/', views.InvitationStatsView.as_view(), name='invitation_stats'),
    
    # Guests
    path('<slug:slug>/guests/', views.GuestListView.as_view(), name='guest_list'),
    path('<slug:slug>/guests/export/', views.ExportGuestsView.as_view(), name='export_guests'),
    
    # Payment
    path('orders/<uuid:pk>/payment/razorpay/create/', CreateRazorpayOrderView.as_view(), name='create_razorpay_order'),
    path('payment/razorpay/verify/', VerifyRazorpayPaymentView.as_view(), name='verify_razorpay_payment'),
    path('payment/razorpay/webhook/', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
]
