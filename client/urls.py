from django.urls import path

from .views import HealthProfileView, HealthMetricView, AppointmentView, DashboardView, NearbyHospitalsView, SymptomHistoryView

urlpatterns = [
    path('onboarding/', HealthProfileView.as_view(), name='user_onboarding'),
    path('metrics/', HealthMetricView.as_view(), name='health_metrics'),
    path('appointments/', AppointmentView.as_view(), name='appointments'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('nearby_hospitals/', NearbyHospitalsView.as_view(), name='nearby_hospitals'),
    path('symptom_history/', SymptomHistoryView.as_view(), name='symptom_history'),
]
