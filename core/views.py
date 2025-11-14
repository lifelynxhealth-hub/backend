from .models import Notification
from .serializers import NotificationSerializer
from .pagination import StandardResultsSetPagination
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from ai.chatbot_simple import LifelynxAISimple
import logging
from client.models import HealthProfile

logger = logging.getLogger(__name__)

# Create your views here.

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() in ['true', '1']:
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() in ['false', '0']:
                queryset = queryset.filter(is_read=False)
        
        return queryset

class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by('-last_activity')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ChatSessionListSerializer
        return ChatSessionSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        chat_session = self.get_object()
        message_text = request.data.get('message', '').strip()
        
        if not message_text:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=chat_session,
            sender='user',
            message=message_text
        )
        
        # Process with AI
        ai_bot = LifelynxAISimple()
        try:
            result = ai_bot.generate_response(
                message_text, 
                request.user.preferred_language,
                {
                    'blood_type': request.user.blood_type,
                    'genotype': request.user.genotype,
                    'allergies': request.user.allergies
                }
            )
            
            # Save AI response
            ai_message = ChatMessage.objects.create(
                session=chat_session,
                sender='ai',
                message=result['response']
            )
            
            # Update session title if it's the first message
            if not chat_session.title:
                chat_session.title = message_text[:50] + "..." if len(message_text) > 50 else message_text
                chat_session.save()
            
            # Create health record if symptoms detected
            if result['symptoms_detected']:
                HealthRecord.objects.create(
                    user=request.user,
                    chat_session=chat_session,
                    symptoms=', '.join(result['symptoms_detected']),
                    diagnosis=', '.join([d['disease'] for d in result['diagnosis']]),
                    confidence_score=result['diagnosis'][0]['confidence'] if result['diagnosis'] else 0,
                    is_emergency=result['is_emergency']
                )
            
            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'ai_response': ChatMessageSerializer(ai_message).data,
                'health_data': result
            })
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return Response(
                {'error': 'System dey busy now. Try again small time.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def book_okada(self, request, pk=None):
        chat_session = self.get_object()
        phc_id = request.data.get('phc_id')
        
        if not phc_id:
            return Response({'error': 'PHC ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        phc = get_object_or_404(PHC, id=phc_id)
        
        # Simulate booking (same as before)
        import random
        drivers = [
            {'name': 'Chukwu Emeka', 'phone': '+2348012345678', 'plate': 'LAG123AB'},
            {'name': 'Adeola Johnson', 'phone': '+2348023456789', 'plate': 'LAG456CD'},
            {'name': 'Bala Mohammed', 'phone': '+2348034567890', 'plate': 'LAG789EF'},
        ]
        driver = random.choice(drivers)
        
        booking = OkadaBooking.objects.create(
            user=request.user,
            chat_session=chat_session,
            phc=phc,
            driver_name=driver['name'],
            driver_phone=driver['phone'],
            vehicle_plate=driver['plate'],
            fare=400.00,
            estimated_arrival=random.randint(4, 8)
        )
        
        # Add booking message to chat
        booking_message = ChatMessage.objects.create(
            session=chat_session,
            sender='ai',
            message=f"Okada don dey come! Driver {driver['name']} go reach you for {booking.estimated_arrival} minutes. "
                   f"Plate number: {driver['plate']}. Total fare: N{booking.fare}. "
                   f"Driver go call you for {driver['phone']}."
        )
        
        return Response({
            'booking': OkadaBookingSerializer(booking).data,
            'ai_message': ChatMessageSerializer(booking_message).data
        })

class QuickChatView(APIView):
    """
    For quick chat without session management (like WhatsApp)
    """
    def __init__(self):
        super().__init__()
        self.ai_bot = LifelynxAISimple()
    
    def post(self, request):
        user = request.user
        message = request.data.get('message', '')
        language = request.data.get('language', user.preferred_language)
        
        if not message:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self.ai_bot.generate_response(
                message, 
                language,
                {
                    'blood_type': user.blood_type,
                    'genotype': user.genotype,
                    'allergies': user.allergies
                }
            )
            
            # Create health record if symptoms detected
            if result['symptoms_detected']:
                HealthProfile.objects.create(
                    user=user,
                    symptoms=', '.join(result['symptoms_detected']),
                    diagnosis=', '.join([d['disease'] for d in result['diagnosis']]),
                    confidence_score=result['diagnosis'][0]['confidence'] if result['diagnosis'] else 0,
                    is_emergency=result['is_emergency']
                )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Quick chat error: {str(e)}")
            return Response(
                {'error': 'System dey busy now. Try again small time.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )