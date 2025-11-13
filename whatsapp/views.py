# whatsapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View
import json
from ai.chatbot_simple import LifelynxAISimple
from accounts.models import User
from client.models import ChatSession, ChatMessage
from client.models import HealthProfile as HealthRecord
import logging

logger = logging.getLogger(__name__)

class WhatsAppWebhook(View):
    def __init__(self):
        super().__init__()
        self.ai_bot = LifelynxAISimple()
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            message = data.get('Body', '').strip()
            from_number = data.get('From', '').replace('whatsapp:', '')
            
            logger.info(f"Received WhatsApp message from {from_number}: {message}")
            
            # Get or create user
            user, created = User.objects.get_or_create(
                phone_number=from_number,
                defaults={
                    'username': from_number, 
                    'preferred_language': 'pidgin'
                }
            )
            
            # Get or create active chat session for WhatsApp
            chat_session, created = ChatSession.objects.get_or_create(
                user=user,
                is_active=True,
                defaults={'title': 'WhatsApp Chat'}
            )
            
            # Handle special commands
            if message.upper() == 'OKADA':
                response = self._handle_okada_booking(user, chat_session)
            elif message.upper() in ['HI', 'HELLO', 'HELLO O']:
                response = self._get_welcome_message(user.preferred_language)
                
                # Save welcome message
                ChatMessage.objects.create(
                    session=chat_session,
                    sender='ai',
                    message=response
                )
            else:
                # Save user message
                ChatMessage.objects.create(
                    session=chat_session,
                    sender='user',
                    message=message
                )
                
                # Process with AI
                result = self.ai_bot.generate_response(
                    message, 
                    user.preferred_language,
                    {
                        'blood_type': user.blood_type,
                        'genotype': user.genotype,
                        'allergies': user.allergies
                    }
                )
                
                response = result['response']
                
                # Save AI response
                ChatMessage.objects.create(
                    session=chat_session,
                    sender='ai',
                    message=response
                )
                
                # Create health record if symptoms detected
                if result['symptoms_detected']:
                    HealthRecord.objects.create(
                        user=user,
                        chat_session=chat_session,
                        symptoms=', '.join(result['symptoms_detected']),
                        diagnosis=', '.join([d['disease'] for d in result['diagnosis']]),
                        confidence_score=result['diagnosis'][0]['confidence'] if result['diagnosis'] else 0,
                        is_emergency=result['is_emergency']
                    )
            
            return JsonResponse({'response': response})
            
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {str(e)}")
            return JsonResponse({
                'response': 'System dey busy now. Try again small time.'
            })
    
    def _get_welcome_message(self, language):
        welcome_messages = {
            'pidgin': "Welcome to Lifelynx! I be your village doctor for pocket. Tell me how you dey feel or wetin dey worry you.",
            'yoruba': "Kaabo si Lifelynx! Emi ni dokita ilu re ninu apo re. So fun mi bi o se n wa tabi kini o n wahala.",
            'igbo': "Nnọọ na Lifelynx! Abụ m dọkịta obodo gị n'akpa gị. Gwa m otú ị na-adị ma ọ bụ ihe na-enye gị nsogbu.",
            'hausa': "Barka da zuwa Lifelynx! Ni ne likitan ƙauyenka a cikin aljihunka. Faɗa mini yadda kake ji ko abin da ke damunka.",
            'english': "Welcome to Lifelynx! I'm your village doctor in your pocket. Tell me how you're feeling or what's bothering you."
        }
        return welcome_messages.get(language, welcome_messages['pidgin'])
    
    def _handle_okada_booking(self, user, chat_session):
        from client.models import PHC, OkadaBooking, ChatMessage
        
        nearest_phc = PHC.objects.filter(is_active=True).first()
        if nearest_phc:
            # Create booking
            booking = OkadaBooking.objects.create(
                user=user,
                chat_session=chat_session,
                phc=nearest_phc,
                driver_name="Available Driver",
                driver_phone="+234800000000",
                vehicle_plate="LAG123XYZ",
                fare=400.00,
                estimated_arrival=7
            )
            
            response = f"Okada don dey come! Driver {booking.driver_name} go reach you for {booking.estimated_arrival} minutes. " \
                      f"Plate number: {booking.vehicle_plate}. Total fare: N{booking.fare}. " \
                      f"Driver go call you for {booking.driver_phone}."
            
            # Save booking message
            ChatMessage.objects.create(
                session=chat_session,
                sender='ai',
                message=response
            )
            
            return response
        else:
            return "Sorry, no PHC dey available for your area now. Try again later."