from django.urls import path

from . import views

urlpatterns = [
    path('', views.EnquiryCreateView.as_view(), name='enquiry_create'),
]
