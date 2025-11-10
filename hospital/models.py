from django.db import models

from accounts.models import User

# Create your models here.

class Hospital(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)
    website = models.URLField(blank=True, null=True)

    hospital_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique ID such as HMB, MDCN, or NHIS registration number"
    )

    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Latitude coordinate for map display"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Longitude coordinate for map display"
    )

    SPECIALTY_CHOICES = [
        ('general', 'General Medicine'),
        ('pediatrics', 'Pediatrics'),
        ('gynecology', 'Gynecology'),
        ('cardiology', 'Cardiology'),
        ('dermatology', 'Dermatology'),
        ('dentistry', 'Dentistry'),
        ('surgery', 'Surgery'),
        ('orthopedics', 'Orthopedics'),
        ('psychiatry', 'Psychiatry'),
        ('ophthalmology', 'Ophthalmology'),
        ('ENT', 'Ear, Nose & Throat'),
        ('others', 'Others'),
    ]
    specialties = models.JSONField(
        default=list,
        help_text="List of specialties available, e.g. ['pediatrics', 'surgery']"
    )

    verified = models.BooleanField(default=False)
    date_registered = models.DateTimeField(auto_now_add=True)
    approved_by_admin = models.BooleanField(default=False)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="hospital",
        help_text="User account that manages this hospital profile"
    )
    
    @property
    def google_maps_link(self):
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

    class Meta:
        ordering = ['name']
