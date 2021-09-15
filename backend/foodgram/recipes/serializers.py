from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from users.models import User
from users.serializers import UserSerializer

from .models import (
    Amount, Favorite, Ingredient, Recipe, ShoppingCart, Subscription, Tag,
)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class AmountSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.SerializerMethodField()
    ingredient_unit = serializers.SerializerMethodField()
    amount = serializers.FloatField()

    class Meta:
        fields = (
            'ingredient_name', 'amount', 'ingredient_unit'
        )
        model = Amount
        validators = [UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=['recipe', 'ingredient']
        ), ]

    def get_ingredient_name(self, obj):
        return obj.ingredient.name

    def get_ingredient_unit(self, obj):
        return obj.ingredient.measurement_unit


class BaseRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(source='get_author', many=False, read_only=True)
    tags = SlugRelatedField(
        slug_field='id', many=True, queryset=Tag.objects.all()
    )
    image = serializers.ImageField(
        max_length=None, use_url=True, allow_null=True, required=False
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'author', 'name', 'image', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user_id = self.context['request'].user.id
        return int(
            Favorite.objects.filter(user__id=user_id, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user_id = self.context['request'].user.id
        return int(ShoppingCart.objects.filter(
            user__id=user_id, recipe=obj
        ).exists())


class RecipeSerializer(BaseRecipeSerializer):
    ingredients = AmountSerializer(
        source='ingredient_set', many=True, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'author', 'name', 'image', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
            'cooking_time'
        )


class RecipeCreateSerializer(BaseRecipeSerializer):
    ingredients = AmountSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'author', 'name', 'image', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
            'cooking_time'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag
        lookup_field = 'id'


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='id',
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    recipe = serializers.SlugRelatedField(
        queryset=Recipe.objects.all(), slug_field='id',
    )

    class Meta:
        exclude = ('id',)
        model = Favorite
        lookup_field = 'id'
        validators = [UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=['user', 'recipe']
        ), ]


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('name', 'image', 'text', 'cooking_time')
        model = Recipe


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='id',
        queryset=User.objects.all(),
        default=serializers.CurrentUserDefault()
    )
    author = serializers.SlugRelatedField(
        queryset=User.objects.all(), slug_field='id',
    )
    recipes = ShortRecipeSerializer(
        source='subscribe_set', many=True, read_only=True,
    )
    username = serializers.SerializerMethodField()

    class Meta:
        fields = ('recipes', 'user', 'author', 'username')
        model = Subscription
        validators = [UniqueTogetherValidator(
            queryset=Subscription.objects.all(),
            fields=['user', 'author']
        ), ]

    def get_username(self, obj):
        return obj.author.username


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ('id',)
        model = ShoppingCart
        lookup_field = 'id'
        validators = [UniqueTogetherValidator(
            queryset=ShoppingCart.objects.all(),
            fields=['user', 'recipe']
        ), ]


class SubscribeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'recipes', 'recipes_count', 'is_subscribed'
        )
        model = User
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_recipes(self, obj):
        limit = 10
        try:
            limit = self.context['request'].query_params['recipes_limit']
        except Exception:
            pass
        queryset = obj.recipes.all()[:int(limit)]
        serializer = ShortRecipeSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        return int(Subscription.objects.filter(
            author=obj, user__id=self.context['request'].user.id
        ).exists())
