from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Hospital
from .serializers import HospitalSerializer
from core.utils import geocode_address
from core.models import Appointment, Notification
from core.serializers import HospitalAppointmentSerializer
from core.pagination import StandardResultsSetPagination

# Create your views here.

class HospitalProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = HospitalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if not user.is_hospital:
            raise PermissionDenied("Only hospital accounts can access this resource.")

        hospital, created = Hospital.objects.get_or_create(owner=user)
        return hospital

    def perform_update(self, serializer):
        instance = serializer.instance
        address = serializer.validated_data.get('address', instance.address)
        city = serializer.validated_data.get('city', instance.city)
        state = serializer.validated_data.get('state', instance.state)
        
        if (address != instance.address or city != instance.city or state != instance.state) and address and city and state:
            lat, lng = geocode_address(address, city, state)
            if (lat, lng):
                serializer.save(owner=self.request.user,
                                latitude=lat,
                                longitude=lng)
            else:
                serializer.save(owner=self.request.user)
        else:
            serializer.save(owner=self.request.user)

    def perform_create(self, serializer):
        address = serializer.validated_data.get('address')
        city = serializer.validated_data.get('city')
        state = serializer.validated_data.get('state')
        latitude = longitude = None

        if address and city and state:
            lat, lng = geocode_address(address, city, state)
            if (lat, lng):
                latitude = lat
                longitude =lng

        serializer.save(owner=self.request.user, latitude=latitude, longitude=longitude)

class HospitalAppointmentListView(generics.ListAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(hospital__owner=user).order_by('-appointment_date', '-appointment_time')

class HospitalAppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(hospital__owner=user)
    
class HospitalAppointmentUpdateStatusView(generics.UpdateAPIView):
    serializer_class = HospitalAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(hospital__owner=user)

    def patch(self, request, *args, **kwargs):
        appointment = self.get_object()
        status_value = request.data.get('status')

        if status_value not in dict(Appointment.STATUS_CHOICES):
            return Response({"error": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = appointment.status
        appointment.status = status_value
        appointment.save()

        subject_patient = f"Lifelynx: Your Appointment Status with {appointment.hospital.name} Updated"
        context_patient = {
            "user": appointment.patient,
            "appointment": appointment,
            "old_status": old_status,
            "new_status": status_value,
        }
        text_content = render_to_string('emails/appointment_status_update.txt', context_patient)
        html_content = render_to_string('emails/appointment_status_update.html', context_patient)

        email_patient = EmailMultiAlternatives(
            subject=subject_patient,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.patient.email]
        )
        email_patient.attach_alternative(html_content, "text/html")
        email_patient.send(fail_silently=True)

        Notification.objects.create(
            recipient=appointment.patient,
            title="Appointment Status Updated",
            message=(
                f"Your appointment with {appointment.hospital.name} for {appointment.specialty} on "
                f"{appointment.appointment_date} at {appointment.appointment_time} has been updated to '{status_value}'."
            )
        )

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

class HospitalDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        if not hasattr(user, 'is_hospital'):
            return Response({"error": "Only hospitals can access this dashboard."}, status=403)

        hospital = user.hospital
        today = timezone.localdate()
        todays_appointments = Appointment.objects.filter(
            hospital=hospital,
            appointment_date=today
        ).order_by('appointment_time')
        patients_count = todays_appointments.values('patient').distinct().count()
        pending_count = Appointment.objects.filter(
            hospital=hospital,
            status='pending'
        ).count()

        appointments_data = HospitalAppointmentSerializer(todays_appointments, many=True).data

        dashboard_data = {
            "patients_count": patients_count,
            "pending_appointments_count": pending_count,
            "todays_appointments": appointments_data
        }

        return Response(dashboard_data, status=200)
