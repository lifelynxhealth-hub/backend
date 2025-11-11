from django.urls import path
from .views import PatientRegisterView, HospitalRegisterView, LoginView, VerifyEmailView, ForgotPasswordView, ResetPasswordView

urlpatterns = [
    path('register/patient/', PatientRegisterView.as_view(), name='register_patient'),
    path('register/hospital/', HospitalRegisterView.as_view(), name='register_hospital'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
