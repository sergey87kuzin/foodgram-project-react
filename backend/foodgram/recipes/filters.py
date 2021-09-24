from django_filters import rest_framework as filters

from .models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.MultipleChoiceFilter(
        choices=Tag.objects.all().values_list('slug', 'name'),
        field_name='tags__slug', label='тэги'
    )
    author = filters.CharFilter(
        field_name='author__id', label='автор'
    )
    is_favorited = filters.BooleanFilter(
        label='в избранных', method='check_fav'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        label='в списке покупок', method='check_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited',
                  'is_in_shopping_cart', 'tags']

    def check_fav(self, queryset, name, value):
        user_id = self.request.user.id
        queryset = Recipe.objects.all()
        if value is False:
            queryset = queryset.exclude(favorites__user__id=user_id)
        elif value is True:
            queryset = queryset.filter(favorites__user__id=user_id)
        return queryset

    def check_cart(self, queryset, name, value):
        user_id = self.request.user.id
        queryset = Recipe.objects.all()
        if value is False:
            queryset = queryset.exclude(carts__user__id=user_id)
        elif value is True:
            queryset = queryset.filter(carts__user__id=user_id)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name', label='name', lookup_expr='gte'
    )

    class Meta:
        model = Ingredient
        fields = ['name']
