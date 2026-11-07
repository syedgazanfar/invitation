"""
Public enquiry endpoint (no auth).
"""
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Enquiry
from .serializers import EnquiryCreateSerializer
from .services import EnquiryService

SUCCESS_MESSAGE = "Thanks! We've received your enquiry and will contact you on WhatsApp shortly."


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class EnquiryCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'enquiry'

    def get_throttles(self):
        # Only rate-limit submissions, not the options lookup.
        if self.request.method == 'POST':
            return [ScopedRateThrottle()]
        return []

    def get(self, request):
        """Form options for the frontend."""
        return Response({
            'success': True,
            'data': {
                'event_types': [{'value': v, 'label': l} for v, l in Enquiry.EventType.choices],
            },
        })

    def post(self, request):
        serializer = EnquiryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'message': 'Please correct the errors below.', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = dict(serializer.validated_data)
        honeypot = data.pop('website', '')
        if honeypot:
            # Pretend success to bots, store nothing.
            return Response({'success': True, 'message': SUCCESS_MESSAGE}, status=status.HTTP_201_CREATED)

        enquiry = EnquiryService.create_enquiry(
            data,
            source_ip=_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        return Response(
            {'success': True, 'message': SUCCESS_MESSAGE, 'data': {'id': str(enquiry.id)}},
            status=status.HTTP_201_CREATED,
        )
