"""
URL configuration for plans app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Plans
    path('', views.PlanListView.as_view(), name='plan_list'),
    path('<str:code>/', views.PlanDetailView.as_view(), name='plan_detail'),
    
    # Categories
    path('categories/list', views.CategoryListView.as_view(), name='category_list'),
    
    # Templates
    path('templates/all', views.TemplateListView.as_view(), name='template_list'),
    path('templates/featured', views.get_featured_templates, name='featured_templates'),
    path('templates/<uuid:pk>/', views.TemplateDetailView.as_view(), name='template_detail'),
    path('templates/by-plan/<str:plan_code>/', views.get_templates_by_plan, name='templates_by_plan'),
]
