from django.urls import path
from .views import HospitalProfileView

urlpatterns = [
    path('onboarding/', HospitalProfileView.as_view(), name='hospital_onboarding'),
]
