from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.views import APIView
from .serializers import RegisterSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .models import User

# Create your views here.

class BaseRegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    user_type = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            context={"user_type": self.user_type}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Registration successful! Please check your email to verify your account."},
            status=status.HTTP_201_CREATED
        )

class PatientRegisterView(BaseRegisterView):
    user_type = "patient"

class HospitalRegisterView(BaseRegisterView):
    user_type = "hospital"

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'email': user.email,
                'full_name': user.full_name,
                'is_hospital': user.is_hospital,
                'is_patient': user.is_patient,
            }
        }, status=status.HTTP_200_OK)

class VerifyEmailView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'error': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)

            if not user.is_active:
                user.is_active = True
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Email verified successfully.',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user_type': 'hospital' if user.is_hospital else 'patient'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Email already verified.',
                    'user_type': 'hospital' if user.is_hospital else 'patient'
                }, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password reset link sent! Please check your email."},
            status=status.HTTP_200_OK,
        )

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Password reset successful! You can now log in."},
            status=status.HTTP_200_OK,
        )
