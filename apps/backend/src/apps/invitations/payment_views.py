"""
Payment Integration with Razorpay
"""
import json
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Order, OrderStatus


class CreateRazorpayOrderView(APIView):
    """Create a Razorpay order for payment"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
            
            if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT]:
                return Response({
                    'success': False,
                    'message': 'Order cannot be paid for at this stage'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize Razorpay client
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(order.payment_amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': order.order_number,
                'notes': {
                    'order_id': str(order.id),
                    'user_id': str(request.user.id),
                    'plan': order.plan.name,
                }
            })
            
            return Response({
                'success': True,
                'data': {
                    'order_id': razorpay_order['id'],
                    'amount': order.payment_amount,
                    'currency': 'INR',
                    'key_id': settings.RAZORPAY_KEY_ID,
                    'prefill': {
                        'name': request.user.full_name or request.user.username,
                        'email': request.user.email or '',
                        'contact': request.user.phone,
                    }
                }
            })
            
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """Handle Razorpay webhook for payment confirmation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            # Verify webhook signature
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
            signature = request.headers.get('X-Razorpay-Signature')
            
            body = request.body.decode('utf-8')
            
            try:
                client.utility.verify_webhook_signature(body, signature, webhook_secret)
            except Exception:
                return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse webhook data
            data = json.loads(body)
            event = data.get('event')
            
            if event == 'payment.captured':
                payment = data.get('payload', {}).get('payment', {}).get('entity', {})
                order_notes = payment.get('notes', {})
                order_id = order_notes.get('order_id')
                
                if order_id:
                    try:
                        order = Order.objects.get(id=order_id)
                        order.payment_status = 'RECEIVED'
                        order.payment_method = 'RAZORPAY'
                        order.payment_notes = f"Payment ID: {payment.get('id')}"
                        order.status = OrderStatus.PENDING_APPROVAL
                        order.save()
                        
                        # TODO: Send notification to admin
                        
                    except Order.DoesNotExist:
                        pass
            
            return Response({'status': 'ok'})
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyRazorpayPaymentView(APIView):
    """Verify payment signature from frontend"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_signature = request.data.get('razorpay_signature')
            order_id = request.data.get('order_id')
            
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Update order
            order = Order.objects.get(id=order_id, user=request.user)
            order.payment_status = 'RECEIVED'
            order.payment_method = 'RAZORPAY'
            order.payment_notes = f"Payment ID: {razorpay_payment_id}"
            order.status = OrderStatus.PENDING_APPROVAL
            order.save()
            
            return Response({
                'success': True,
                'message': 'Payment successful',
                'data': {
                    'order_id': order.id,
                    'status': order.status
                }
            })
            
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
