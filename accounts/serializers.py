from rest_framework import serializers
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    agree_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'password', 'confirm_password', 'agree_terms']

    def validate_agree_terms(self, value):
        if not value:
            raise serializers.ValidationError("You must agree to the terms to continue.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('agree_terms')
        user = User.objects.create_user(**validated_data)
        user.is_hospital = False
        user.is_patient = True
        user.is_active = False
        user.save()

        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)

        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_mail(
            subject="LifeLynx: Verify your email address",
            message= (
                f"Hi {user.full_name},\n\n"
                f"Welcome to LifeLynx! Please verify your email by clicking the link below:\n\n"
                f"{verify_url}\n\n"
                f"If you didn't register for this account, you can safely ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account not verified. Please check your email.")

        data['user'] = user
        return data
