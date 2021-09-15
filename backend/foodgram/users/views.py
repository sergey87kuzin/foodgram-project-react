from http import HTTPStatus

from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from recipes.models import Subscription
from recipes.serializers import SubscribeSerializer, SubscriptionSerializer
from recipes.validators import validate_subscribe

from .models import User
from .serializers import UserSerializer


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    pagination_class = PageNumberPagination
    lookup_field = 'id'
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        instance = request.user
        serializer = UserSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        instance = request.user
        new_password = request.data['new_password']
        data = {'password': new_password}
        serializer = UserSerializer(instance, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        context = {'request': request}
        queryset = User.objects.filter(followings__user__id=request.user.id)
        serializer = SubscribeSerializer(
            queryset, many=True, context=context
        )
        return Response(serializer.data)


@api_view(['get', 'delete'])
def subscription_view(request, user_id):
    user = request.user
    author = get_object_or_404(
        User, id=user_id,
    )
    if request.method == 'GET':
        try:
            validate_subscribe(user, author)
        except ValidationError:
            return Response(
                'Cant subscribe your account', status=HTTPStatus.BAD_REQUEST
            )
        data = {'user': user.id, 'author': author.id, 'request': request}
        serializer = SubscriptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)
    elif request.method == 'DELETE':
        try:
            instance = Subscription.objects.get(author=author, user=user)
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        except Exception:
            return Response(
                'You are not subscribed', status=HTTPStatus.BAD_REQUEST
            )