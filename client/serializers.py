from rest_framework import serializers
from django.utils import timezone
import datetime

from .models import HealthProfile, HealthMetric, Appointment

class HealthProfileSerializer(serializers.ModelSerializer):
    bmi = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HealthProfile
        exclude = ['user', 'created_at', 'updated_at']

    def get_bmi(self, obj):
        bmi = obj.calculate_bmi()
        return bmi if bmi else None

    def validate(self, data):
        height = data.get('height')
        weight = data.get('weight')
        if height and height <= 0:
            raise serializers.ValidationError({"height": "Height must be a positive value."})
        if weight and weight <= 0:
            raise serializers.ValidationError({"weight": "Weight must be a positive value."})
        return data

class HealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthMetric
        exclude = ['user', 'updated_at']

    def validate(self, data):
        systolic = data.get('systolic_bp')
        diastolic = data.get('diastolic_bp')
        heart_rate = data.get('heart_rate')
        temperature = data.get('temperature')

        if systolic and (systolic < 50 or systolic > 300):
            raise serializers.ValidationError({"systolic_bp": "Invalid systolic pressure value."})
        if diastolic and (diastolic < 30 or diastolic > 150):
            raise serializers.ValidationError({"diastolic_bp": "Invalid diastolic pressure value."})
        if heart_rate and (heart_rate < 30 or heart_rate > 200):
            raise serializers.ValidationError({"heart_rate": "Invalid heart rate value."})
        if temperature and (temperature < 20 or temperature > 50):
            raise serializers.ValidationError({"temperature": "Invalid temperature value."})
        return data

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
