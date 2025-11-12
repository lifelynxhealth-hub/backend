from rest_framework import serializers

from .models import HealthProfile, HealthMetric, ChatSession
from hospital.models import Hospital

class HealthProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    bmi = serializers.SerializerMethodField(read_only=True)
    google_maps_link = serializers.ReadOnlyField()

    class Meta:
        model = HealthProfile
        exclude = ['user', 'created_at', 'updated_at']
        read_only_fields = ['google_maps_link']

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
        exclude = ['user', 'created_at']

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

class NearbyHospitalSerializer(serializers.ModelSerializer):
    distance_km = serializers.FloatField(read_only=True)
    specialties = serializers.ListField(child=serializers.CharField(), read_only=True)
    google_maps_link = serializers.ReadOnlyField()

    class Meta:
        model = Hospital
        fields = ['id', 'name', 'address', 'city', 'state', 'specialties', 'google_maps_link', 'distance_km']

class ChatSessionSummarySerializer(serializers.ModelSerializer):
    symptoms_reported = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "title",
            "started_at",
            "last_activity",
            "is_active",
            "symptoms_reported",
        ]

    def get_symptoms_reported(self, obj):
        report = getattr(obj, "report", None)
        if report and report.exists():
            return report.first().symptoms_reported
        return None
