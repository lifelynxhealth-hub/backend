from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import HealthProfile, HealthMetric, ChatSession, HealthReport
from .serializers import HealthProfileSerializer, HealthMetricSerializer, AppointmentSerializer, NearbyHospitalSerializer, ChatSessionSummarySerializer
from hospital.models import Hospital
from core.pagination import StandardResultsSetPagination
from core.utils import geocode_address, haversine_distance
from core.models import Appointment, Notification

# Create your views here.

class HealthProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = HealthProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if not user.is_patient:
            raise PermissionDenied("Only patients can have a health profile.")
        profile, created = HealthProfile.objects.get_or_create(user=user)
        return profile

    def perform_update(self, serializer):
        instance = serializer.instance
        address = serializer.validated_data.get('address', instance.address)
        city = serializer.validated_data.get('city', instance.city)
        state = serializer.validated_data.get('state', instance.state)

        if (address != instance.address or city != instance.city or state != instance.state) and address and city and state:
            lat, lng = geocode_address(address, city, state)
            serializer.save(latitude=lat, longitude=lng)
        else:
            serializer.save()

    def perform_create(self, serializer):
        address = serializer.validated_data.get('address')
        city = serializer.validated_data.get('city')
        state = serializer.validated_data.get('state')
        latitude = longitude = None

        if address and city and state:
            lat, lng = geocode_address(address, city, state)
            latitude, longitude = lat, lng

        serializer.save(user=self.request.user, latitude=latitude, longitude=longitude)

class HealthMetricView(generics.GenericAPIView):
    serializer_class = HealthMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        metrics = HealthMetric.objects.filter(user=request.user).order_by('-created_at')
        if not metrics.exists():
            return Response({"message": "No health metrics found."}, status=status.HTTP_404_NOT_FOUND)
            
        page = self.paginate_queryset(metrics)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            "message": "Health metric added successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

class AppointmentView(generics.GenericAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        appointments = Appointment.objects.filter(patient=request.user).order_by('-created_at')
        if not appointments.exists():
            return Response({"message": "No appointments found."}, status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(appointments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(patient=request.user)

        subject_patient = f"Lifelynx: Appointment Confirmation with {appointment.hospital.name}"
        subject_hospital = f"Lifelynx: New Appointment from {request.user.full_name}"

        context_patient = {
            "user": request.user,
            "appointment": appointment
        }
        context_hospital = {
            "user": request.user,
            "appointment": appointment
        }

        text_content_patient = render_to_string('emails/appointment_confirmation.txt', context_patient)
        html_content_patient = render_to_string('emails/appointment_confirmation.html', context_patient)

        text_content_hospital = render_to_string('emails/new_appointment_hospital.txt', context_hospital)
        html_content_hospital = render_to_string('emails/new_appointment_hospital.html', context_hospital)

        email_patient = EmailMultiAlternatives(
            subject=subject_patient,
            body=text_content_patient,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[request.user.email]
        )
        email_patient.attach_alternative(html_content_patient, "text/html")
        email_patient.send(fail_silently=True)

        email_hospital = EmailMultiAlternatives(
            subject=subject_hospital,
            body=text_content_hospital,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appointment.hospital.email]
        )
        email_hospital.attach_alternative(html_content_hospital, "text/html")
        email_hospital.send(fail_silently=True)

        Notification.objects.create(
            recipient=request.user,
            title="Appointment Booked",
            message=f"Your appointment with {appointment.hospital.name} for {appointment.specialty} on "
                    f"{appointment.appointment_date} at {appointment.appointment_time} has been booked."
        )

        Notification.objects.create(
            recipient=appointment.hospital.owner,
            title="New Appointment",
            message=f"{request.user.full_name} has booked an appointment for {appointment.specialty} on "
                    f"{appointment.appointment_date} at {appointment.appointment_time}."
        )

        return Response({
            "message": "Appointment created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        latest_metric = HealthMetric.objects.filter(user=user).order_by('-created_at').first()
        metric_data = None
        if latest_metric:
            metric_data = HealthMetricSerializer(latest_metric).data
            profile = HealthProfile.objects.filter(user=user).first()
            if profile and profile.calculate_bmi():
                metric_data["bmi"] = profile.calculate_bmi()
            else:
                metric_data["bmi"] = None

        last_sessions = ChatSession.objects.filter(user=user).order_by('-last_activity')[:3]
        chat_data = [
            {
                "id": session.id,
                "title": session.title or "Chat Session",
                "last_activity": session.last_activity,
            }
            for session in last_sessions
        ]

        last_appointments = Appointment.objects.filter(user=user).order_by('-appointment_date', '-appointment_time')[:2]
        appointment_data = AppointmentSerializer(last_appointments, many=True).data

        dashboard_data = {
            "user": user,
            "health_metric": metric_data,
            "recent_symptoms": chat_data,
            "appointments": appointment_data
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)

class NearbyHospitalsView(generics.ListAPIView):
    serializer_class = NearbyHospitalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        try:
            profile = HealthProfile.objects.get(user=user)
            user_lat = profile.latitude
            user_lon = profile.longitude
        except HealthProfile.DoesNotExist:
            return Hospital.objects.none()

        if not user_lat or not user_lon:
            return Hospital.objects.none()

        hospitals = Hospital.objects.filter(verified=True, approved_by_admin=True, latitude__isnull=False, longitude__isnull=False)

        hospital_list = []
        for hospital in hospitals:
            distance = haversine_distance(user_lat, user_lon, float(hospital.latitude), float(hospital.longitude))
            hospital.distance_km = round(distance, 2)
            hospital_list.append(hospital)

        hospital_list.sort(key=lambda x: x.distance_km)
        return hospital_list

class SymptomHistoryView(generics.GenericAPIView):
    serializer_class = ChatSessionSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        user = request.user

        sessions = ChatSession.objects.filter(user=user).order_by("-last_activity")
        session_count = sessions.count()
        report_count = HealthReport.objects.filter(user=user).count()

        if not sessions.exists():
            return Response(
                {"message": "No chat sessions found."},
                status=status.HTTP_404_NOT_FOUND
            )

        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "summary": {
                    "total_sessions": session_count,
                    "total_reports": report_count,
                },
                "sessions": serializer.data
            })

        serializer = self.get_serializer(sessions, many=True)
        return Response({
            "summary": {
                "total_sessions": session_count,
                "total_reports": report_count,
            },
            "sessions": serializer.data
        }, status=status.HTTP_200_OK)
