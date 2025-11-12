from django.urls import path
from .views import HospitalProfileView, HospitalAppointmentListView, HospitalAppointmentDetailView, HospitalAppointmentUpdateStatusView, HospitalDashboardView

urlpatterns = [
    path('onboarding/', HospitalProfileView.as_view(), name='hospital_onboarding'),
    path('hospital/appointments/', HospitalAppointmentListView.as_view(), name='hospital_appointments'),
    path('hospital/appointments/<int:pk>/', HospitalAppointmentDetailView.as_view(), name='hospital_appointment_detail'),
    path('hospital/appointments/<int:pk>/status/', HospitalAppointmentUpdateStatusView.as_view(), name='hospital_appointment_update_status'),
    path('hospital/dashboard/', HospitalDashboardView.as_view(), name='hospital_dashboard'),
]
