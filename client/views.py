from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from .pagination import StandardResultsSetPagination

from .models import HealthProfile, HealthMetric, Appointment, ChatSession
from .serializers import HealthProfileSerializer, HealthMetricSerializer, AppointmentSerializer

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
        serializer.save(patient=request.user)
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
            "health_metric": metric_data,
            "recent_symptoms": chat_data,
            "appointments": appointment_data
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)
