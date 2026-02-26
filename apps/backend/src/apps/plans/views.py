"""
Views for Plans and Templates
"""
from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .models import Plan, Template, InvitationCategory
from .serializers import (
    PlanSerializer,
    TemplateListSerializer,
    TemplateDetailSerializer,
    InvitationCategorySerializer
)


class PlanListView(generics.ListAPIView):
    """List all active plans"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class PlanDetailView(generics.RetrieveAPIView):
    """Get plan details by code"""
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'


class CategoryListView(generics.ListAPIView):
    """List all invitation categories"""
    queryset = InvitationCategory.objects.filter(is_active=True)
    serializer_class = InvitationCategorySerializer
    permission_classes = [permissions.AllowAny]


class TemplateListView(generics.ListAPIView):
    """List templates with filtering"""
    serializer_class = TemplateListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['plan__code', 'category__code', 'animation_type', 'is_premium']
    ordering_fields = ['use_count', 'created_at', 'name']
    ordering = ['-use_count']
    
    def get_queryset(self):
        queryset = Template.objects.filter(is_active=True)
        
        # Filter by plan code if provided
        plan_code = self.request.query_params.get('plan')
        if plan_code:
            queryset = queryset.filter(plan__code=plan_code.upper())
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__code=category.upper())
        
        return queryset.select_related('plan', 'category')


class TemplateDetailView(generics.RetrieveAPIView):
    """Get template details"""
    queryset = Template.objects.filter(is_active=True)
    serializer_class = TemplateDetailSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_templates_by_plan(request, plan_code):
    """Get all templates for a specific plan"""
    try:
        plan = Plan.objects.get(code=plan_code.upper(), is_active=True)
    except Plan.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Plan not found'
        }, status=404)
    
    # Get templates for this plan and lower plans
    if plan.code == 'LUXURY':
        templates = Template.objects.filter(
            plan__code__in=['BASIC', 'PREMIUM', 'LUXURY'],
            is_active=True
        )
    elif plan.code == 'PREMIUM':
        templates = Template.objects.filter(
            plan__code__in=['BASIC', 'PREMIUM'],
            is_active=True
        )
    else:
        templates = Template.objects.filter(
            plan__code='BASIC',
            is_active=True
        )
    
    # Filter by category if provided
    category = request.query_params.get('category')
    if category:
        templates = templates.filter(category__code=category.upper())
    
    templates = templates.select_related('plan', 'category')
    
    serializer = TemplateListSerializer(templates, many=True)
    return Response({
        'success': True,
        'data': {
            'plan': PlanSerializer(plan).data,
            'templates': serializer.data
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_featured_templates(request):
    """Get featured/popular templates"""
    templates = Template.objects.filter(
        is_active=True
    ).select_related('plan', 'category').order_by('-use_count')[:6]

    serializer = TemplateListSerializer(templates, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })
