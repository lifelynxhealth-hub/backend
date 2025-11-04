from rest_framework import serializers
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime

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
        validated_data['email'] = validated_data['email'].strip().lower()

        user = User.objects.create_user(**validated_data)
        user.is_hospital = False
        user.is_patient = True
        user.is_active = False
        user.save()

        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)

        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        subject = "LifeLynx: Verify your email address"
        html_content = render_to_string("email/verify_email.html", {
            "full_name": user.full_name,
            "verify_url": verify_url,
            "current_year": datetime.now().year,
        })

        text_content = f"""
        Hi {user.full_name},

        Welcome to LifeLynx! Please verify your email by clicking the link below:
        {verify_url}

        If you didn't register for this account, you can safely ignore this email.
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        try:
            email.send(fail_silently=False)
        except Exception as e:
            user.delete()
            raise serializers.ValidationError("Failed to send verification email. Please try again.")

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account not verified. Please check your email.")

        data['user'] = user
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.strip().lower()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account found with this email.")
        return value

    def save(self):
        email = self.validated_data['email'].strip().lower()
        user = User.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        subject = "LifeLynx: Reset your password"
        html_content = render_to_string("email/reset_password.html", {
            "full_name": user.full_name,
            "reset_url": reset_url,
            "current_year": datetime.now().year,
        })

        text_content = f"""
        Hi {user.full_name},

        You requested a password reset. Click the link below to reset your password:
        {reset_url}

        If you didn't request this, you can safely ignore this email.
        """

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        try:
            email.send(fail_silently=False)
        except Exception as e:
            raise serializers.ValidationError("Failed to send email. Please try again.")

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def save(self):
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception:
            raise serializers.ValidationError("Invalid or expired token.")

        user.set_password(new_password)
        user.save()
        return user
