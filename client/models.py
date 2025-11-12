from django.db import models
from django.utils import timezone

from accounts.models import User
from hospital.models import Hospital

# Create your models here.

class HealthProfile(models.Model):

    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    surgical_history = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    lifestyle = models.TextField(blank=True, help_text="Optional notes like diet, exercise habits, smoking, etc.")
    
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def google_maps_link(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    def calculate_bmi(self):
        if self.height and self.weight and self.height > 0:
            height_m = float(self.height) / 100
            bmi = float(self.weight) / (height_m ** 2)
            return round(bmi, 2)
        return None

    def __str__(self):
        return f"{self.user.full_name}'s Health Profile"

class HealthMetric(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="health_metric")
    systolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Systolic blood pressure (mmHg)")
    diastolic_bp = models.PositiveIntegerField(null=True, blank=True, help_text="Diastolic blood pressure (mmHg)")
    heart_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Heart rate (bpm)")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Body temperature (°C)")
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.full_name}'s Health Metrics"

    def blood_pressure_status(self):
        if self.systolic_bp and self.diastolic_bp:
            if self.systolic_bp < 90 or self.diastolic_bp < 60:
                return "Low"
            elif self.systolic_bp <= 120 and self.diastolic_bp <= 80:
                return "Normal"
            elif 120 < self.systolic_bp <= 139 or 80 < self.diastolic_bp <= 89:
                return "Elevated"
            else:
                return "High"
        return None

class Appointment(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    specialty = models.CharField(max_length=100, help_text="The hospital specialty related to this appointment.")
    reason_for_visit = models.TextField(blank=True, help_text="Optional description of why the appointment is being booked.")
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    symptoms = models.TextField(blank=True, help_text="Symptoms provided by the patient.")
    additional_notes = models.TextField(blank=True, help_text="Additional info for the hospital or doctor.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('patient', 'hospital', 'appointment_date', 'appointment_time')

    def __str__(self):
        return f"Appointment with {self.hospital.name} on {self.appointment_date} ({self.patient.full_name})"

    @property
    def is_past(self):
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime < timezone.now()

class ChatSession(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="chat_sessions"
    )
    title = models.CharField(max_length=255, blank=True, help_text="Optional title for the chat session.")
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"ChatSession ({self.user.username}) - {self.title or self.started_at.strftime('%Y-%m-%d %H:%M')}"

class ChatMessage(models.Model):
    
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Assistant'),
    ]

    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name="messages"
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.capitalize()} Message ({self.created_at.strftime('%H:%M:%S')})"

class HealthReport(models.Model):
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="report"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="health_reports")
    
    generated_at = models.DateTimeField(auto_now_add=True)
    symptoms_reported = models.TextField(blank=True)
    duration = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=50, blank=True)
    
    ai_analysis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    vital_signs = models.JSONField(default=dict, blank=True)
    medical_history_summary = models.TextField(blank=True)

    def __str__(self):
        return f"Health Report - {self.user.full_name} ({self.generated_at.strftime('%Y-%m-%d %H:%M')})"
