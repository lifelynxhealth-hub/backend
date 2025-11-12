from django.db import models
from django.utils import timezone

from accounts.models import User
from hospital.models import Hospital

# Create your models here.

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

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.full_name}: {self.title}"
