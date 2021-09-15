from django_filters import rest_framework as filters

from.models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(field_name='tags__slug')
    author = filters.CharFilter(field_name='author__username')

    class Meta:
        model = Recipe
        fields = ['author', 'tags']
