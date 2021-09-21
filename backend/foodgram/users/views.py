from http import HTTPStatus

from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from recipes.models import Subscription
from recipes.paginators import RecipePagination
from recipes.serializers import SubscribeSerializer, SubscriptionSerializer
from recipes.validators import validate_subscribe
from .models import User
from .serializers import ChangePasswordSerializer, UserSerializer


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    pagination_class = RecipePagination
    lookup_field = 'id'
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return ChangePasswordSerializer
        return UserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        instance = request.user
        context = {'request': request}
        serializer = UserSerializer(instance, context=context)
        return Response(serializer.data)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        instance = request.user
        context = {'request': request}
        serializer = ChangePasswordSerializer(instance, context=context)
        try:
            serializer.validate_current_password(request)
        except ValidationError:
            return Response('неверный пароль')
        try:
            new_password = request.data['new_password']
        except Exception:
            return Response('укажите новый пароль')
        data = {'password': new_password}
        serializer = ChangePasswordSerializer(
            instance, data=data, partial=True, context=context)
        try:
            serializer.validate_new_password(request, new_password)
        except ValidationError:
            return Response('новый пароль некорректен')
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(HTTPStatus.OK)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        context = {'request': request}
        queryset = User.objects.filter(followings__user__id=request.user.id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeSerializer(
                page, many=True, context=context
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscribeSerializer(
            queryset, many=True, context=context
        )
        return Response(serializer.data)


@api_view(['get', 'delete'])
def subscription_view(request, user_id):
    user = request.user
    context = {'request': request}
    author = get_object_or_404(
        User, id=user_id,
    )
    if request.method == 'GET':
        try:
            validate_subscribe(user, author)
        except ValidationError:
            return Response(
                'вы не можете подписаться на себя',
                status=HTTPStatus.BAD_REQUEST
            )
        data = {'user': user.id, 'author': author.id}
        serializer = SubscriptionSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscribeSerializer(author, context=context)
        return Response(serializer.data, status=HTTPStatus.CREATED)
    elif request.method == 'DELETE':
        try:
            instance = Subscription.objects.get(author=author, user=user)
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        except Exception:
            return Response(
                'вы не подписаны', status=HTTPStatus.BAD_REQUEST
            )
