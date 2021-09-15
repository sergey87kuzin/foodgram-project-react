import csv

from http import HTTPStatus

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import Amount, Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .paginators import RecipePagination
from .permissions import IsAuthorPermission
from .serializers import (
    AmountSerializer, FavoriteSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeSerializer, ShoppingCartSerializer,
    ShortRecipeSerializer, TagSerializer,
)


class Echo:
    def write(self, value):
        return value


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = RecipePagination
    lookup_field = 'id'
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorPermission]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = RecipeFilter
    filterset_fields = ['author', 'tags']
    search_fields = ['^name']

    def get_queryset(self):
        fav = self.request.query_params.get('is_favorited', None)
        cart = self.request.query_params.get('is_in_shopping_cart', None)
        user_id = self.request.user.id
        queryset = Recipe.objects.all()
        if fav == '1':
            queryset = queryset.filter(favorites__user__id=user_id)
        elif fav == '0':
            queryset = queryset.exclude(favorites__user__id=user_id)
        if cart == '1':
            queryset = queryset.filter(carts__user__id=user_id)
        elif cart == '0':
            queryset = queryset.exclude(carts__user__id=user_id)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def add_amounts(ingr, recipe):
        ingredient = get_object_or_404(Ingredient, id=ingr['id'])
        amount = ingr['amount']
        data = {
            'recipe': recipe.id,
            'ingredient': ingredient.id,
            'amount': amount
        }
        amount_serializer = AmountSerializer(data=data)
        amount_serializer.is_valid(raise_exception=True)
        amount_serializer.save(
            recipe=recipe,
            ingredient=ingredient,
            amount=amount)
        return amount_serializer.data

    def create(self, request, *args, **kwargs):
        author = request.user
        ingredients = request.data['ingredients']
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=author)
        recipe = Recipe.objects.filter(author=author).first()
        headers = self.get_success_headers(serializer.data)
        for ingr in ingredients:
            amount = RecipeViewSet.add_amounts(ingr, recipe)
            serializer.data['ingredients'].append(amount)
        return Response(
            serializer.data, status=HTTPStatus.CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        ingredients = request.data['ingredients']
        instance = self.get_object()
        ingr_instance = Ingredient.objects.filter(
            quantities__recipe=instance
        )
        serializer = self.get_serializer(
            instance, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        for ingredient in ingr_instance:
            amount = get_object_or_404(
                Amount, recipe__id=instance.id, ingredient=ingredient
            )
            amount.delete()
        for ingr in ingredients:
            RecipeViewSet.add_amounts(ingr, instance)
        return Response(
            serializer.data, status=HTTPStatus.OK
        )

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        res_queryset = {}
        queryset = Amount.objects.filter(
            recipe__carts__user__id=request.user.id
        )
        for amount in queryset:
            if amount.ingredient in res_queryset.keys():
                res_queryset[amount.ingredient] += amount.amount
            else:
                res_queryset[amount.ingredient] = amount.amount
        rows = ([ingredient.name, str(res_queryset[ingredient]),
                 ingredient.measurement_unit]
                for ingredient in res_queryset.keys())
        echo_buffer = Echo()
        csv_writer = csv.writer(echo_buffer)
        inputs = (csv_writer.writerow(row) for row in rows)

        response = StreamingHttpResponse(inputs, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="recipes.csv"'
        return response


class CustomViewSet(mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    pass


class TagViewSet(CustomViewSet):
    queryset = Tag.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    serializer_class = TagSerializer


class IngredientViewSet(CustomViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = PageNumberPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
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
                'Not in your favorites', status=HTTPStatus.BAD_REQUEST
            )
