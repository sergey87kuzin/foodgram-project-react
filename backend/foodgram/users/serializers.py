from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers

from recipes.models import Subscription
from .models import User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_subscribed'
        )
        model = User
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            author=obj, user__id=self.context['request'].user.id
        ).exists()


class ChangePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('password', 'id', 'username', 'email', 'first_name',
                  'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        user = User.objects.create_user(
            email=email, password=password, **validated_data
        )
        return user

    def validate_current_password(self, request):
        user = request.user or self.user
        value = request.data.get('current_password')
        assert user is not None
        if value is None:
            raise serializers.ValidationError('укажите пароль пользователя')
        if user.check_password(value):
            return value
        else:
            raise serializers.ValidationError('неверный пароль пользователя')

    def validate_new_password(self, request, value):
        user = request.user or self.user
        assert user is not None

        try:
            validate_password(value, user)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return super().validate(value)
