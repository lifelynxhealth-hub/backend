from django.urls import path

from .views import HealthProfileView, HealthMetricView, AppointmentView

urlpatterns = [
    path('onboarding/', HealthProfileView.as_view(), name='user_onboarding'),
    path('metrics/', HealthMetricView.as_view(), name='health_metrics'),
    path('appointments/', AppointmentView.as_view(), name='appointments'),
]
