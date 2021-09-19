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
