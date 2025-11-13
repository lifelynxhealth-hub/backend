from rest_framework import serializers
from django.utils import timezone
import datetime
from client.models import ChatSession, ChatMessage
from .models import Appointment, Notification

class AppointmentSerializer(serializers.ModelSerializer):
    hospital_name = serializers.ReadOnlyField(source='hospital.name')

    class Meta:
        model = Appointment
        fields = [
            'id', 'hospital', 'hospital_name', 'specialty', 'reason_for_visit',
            'appointment_date', 'appointment_time', 'symptoms',
            'additional_notes', 'status', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']

    def validate(self, data):
        appointment_datetime = timezone.make_aware(
            datetime.datetime.combine(data['appointment_date'], data['appointment_time'])
        )
        if appointment_datetime < timezone.now():
            raise serializers.ValidationError("Appointment time cannot be in the past.")
        return data

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at']

class HospitalAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.ReadOnlyField(source='patient.full_name')

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'specialty', 'reason_for_visit',
            'appointment_date', 'appointment_time', 'symptoms',
            'additional_notes', 'status', 'created_at'
        ]
        read_only_fields = ['created_at', 'patient', 'specialty', 'reason_for_visit',
                            'appointment_date', 'appointment_time', 'symptoms', 'additional_notes']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'created_at']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'started_at', 'last_activity', 'is_active', 'messages', 'message_count']
    
    def get_message_count(self, obj):
        return obj.messages.count()

class ChatSessionListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'started_at', 'last_activity', 'is_active', 'last_message', 'message_count']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        return last_msg.message if last_msg else None
    
    def get_message_count(self, obj):
        return obj.messages.count()