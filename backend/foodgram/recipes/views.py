from http import HTTPStatus

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .models import Amount, Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .paginators import RecipePagination
from .permissions import IsAuthorPermission
from .serializers import (
    FavoriteSerializer, IngredientSerializer, RecipeCreateSerializer,
    RecipeSerializer, ShoppingCartSerializer, ShortRecipeSerializer,
    TagSerializer,
)
from .viewsets import CustomViewSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = RecipePagination
    lookup_field = 'id'
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = RecipeFilter
    filterset_fields = [
        'author', 'tags', 'is_favorited', 'is_in_shopping_cart'
    ]
    search_fields = ['^name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        res_queryset = {}
        queryset = Amount.objects.filter(
            recipe__carts__user__id=request.user.id
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit',
            'amount', named=True
        )
        for amount in queryset:
            name = (
                amount.ingredient__name, amount.ingredient__measurement_unit
            )
            if name in res_queryset:
                res_queryset[name] += amount.amount
            else:
                res_queryset[name] = amount.amount
        rows = ([ingredient[0], str(res_queryset[ingredient]),
                 ingredient[1], '\n']
                for ingredient in res_queryset)
        inputs = (', '.join(row) for row in rows)

        response = StreamingHttpResponse(inputs, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recipes.txt"'
        return response


class TagViewSet(CustomViewSet):
    queryset = Tag.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    serializer_class = TagSerializer


class IngredientViewSet(CustomViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination
    filterset_class = IngredientFilter
    filterset_fields = ['name']
    lookup_field = 'id'
    serializer_class = IngredientSerializer


@api_view(['get', 'delete'],)
def cart_view(request, recipe_id):
    user = request.user
    recipe = get_object_or_404(
        Recipe, id=recipe_id
    )
    if request.method == 'GET':
        data = {'user': user.id, 'recipe': recipe.id}
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        res_serializer = ShortRecipeSerializer(recipe)
        return Response(res_serializer.data, status=HTTPStatus.CREATED)
    elif request.method == 'DELETE':
        instance = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        instance.delete()
        return Response(status=HTTPStatus.NO_CONTENT)


@api_view(['get', 'delete'],)
def favorite_view(request, recipe_id):
    user = request.user
    recipe = get_object_or_404(
        Recipe, id=recipe_id
    )
    if request.method == 'GET':
        data = {'user': user.id, 'recipe': recipe_id}
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        res_serializer = ShortRecipeSerializer(recipe)
        return Response(res_serializer.data, status=HTTPStatus.CREATED)
    elif request.method == 'DELETE':
        try:
            instance = get_object_or_404(Favorite, user=user, recipe=recipe)
            instance.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        except Exception:
            return Response(
                'не в ваших избранных', status=HTTPStatus.BAD_REQUEST
            )
