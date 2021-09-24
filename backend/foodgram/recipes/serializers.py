import base64
import uuid

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from rest_framework.validators import UniqueTogetherValidator

from users.models import User
from users.serializers import UserSerializer
from .models import (
    Amount, Favorite, Ingredient, Recipe, ShoppingCart, Subscription, Tag,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag
        lookup_field = 'id'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class AmountCreateSerializer(serializers.ModelSerializer):
    amount = serializers.FloatField(read_only=True)

    class Meta:
        fields = (
            'amount',
        )
        model = Amount


class AmountSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.FloatField()

    class Meta:
        fields = (
            'id', 'name', 'amount', 'measurement_unit'
        )
        model = Amount
        validators = [UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=['recipe', 'ingredient']
        ), ]


class MyImageField(serializers.ImageField):
    def to_internal_value(self, data):
        format, imgstr = data.split(';base64,')
        file_name = str(uuid.uuid4())[:12]
        ext = format.split('/')[-1]
        data = ContentFile(
            base64.b64decode(imgstr),
            name=file_name + '.' + ext
        )
        django_field = self._DjangoImageField()
        django_field.error_messages = self.error_messages
        return django_field.clean(data)


class BaseRecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(many=False, read_only=True)
    tags = SlugRelatedField(
        slug_field='id', many=True, queryset=Tag.objects.all()
    )
    image = MyImageField(
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

    def create_amount(instance, ingr):
        ingredient = get_object_or_404(Ingredient, id=ingr['id'])
        amount = ingr['amount']
        Amount.objects.create(
            recipe=instance, ingredient=ingredient, amount=amount
        )

    def get_is_favorited(self, obj):
        user_id = self.context['request'].user.id
        return Favorite.objects.filter(user__id=user_id, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user_id = self.context['request'].user.id
        return ShoppingCart.objects.filter(
            user__id=user_id, recipe=obj
        ).exists()


class RecipeSerializer(BaseRecipeSerializer):
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
            'cooking_time'
        )

    def get_ingredients(self, obj):
        instance = obj.quantities
        serializer = AmountSerializer(instance, many=True, read_only=True)
        return serializer.data


class RecipeCreateSerializer(BaseRecipeSerializer):
    ingredients = AmountCreateSerializer(
        many=True, required=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'tags', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'text',
            'cooking_time'
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = self.context['request'].data['ingredients']
        validated_data.pop('ingredients')
        instance = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        instance.tags.set(tags)
        for ingr in ingredients:
            RecipeCreateSerializer.create_amount(instance, ingr)
        return instance

    def update(self, instance, validated_data):
        tags = self.context['request'].data['tags']
        instance.tags.set(tags)
        new_name = validated_data.get('name')
        instance.name = new_name
        new_text = validated_data.get('text')
        instance.text = new_text
        new_image = validated_data.get('image')
        instance.image = new_image
        time = str(validated_data.get('cooking_time'))
        instance.cooking_time = time
        for ingr in instance.quantities.all():
            ingr.delete()
        ingredients = self.context['request'].data['ingredients']
        for ingr in ingredients:
            RecipeSerializer.create_amount(instance, ingr)
        instance.save()
        return instance


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
        fields = '__all__'
        model = Favorite
        lookup_field = 'id'
        validators = [UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=['user', 'recipe']
        ), ]


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
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
    recipes = serializers.SerializerMethodField()

    class Meta:
        fields = ('recipes', 'user', 'author')
        model = Subscription
        validators = [UniqueTogetherValidator(
            queryset=Subscription.objects.all(),
            fields=['user', 'author']
        ), ]

    def get_recipes(self, obj):
        instance = obj.author.recipes
        serializer = ShortRecipeSerializer(instance, many=True, read_only=True)
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
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
            'id', 'username', 'email', 'first_name', 'last_name',
            'recipes', 'recipes_count', 'is_subscribed'
        )
        model = User
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_recipes(self, obj):
        limit = 10
        r_limit = self.context['request'].query_params.get('recipes_limit')
        if r_limit:
            limit = r_limit
        queryset = obj.recipes.all()[:int(limit)]
        serializer = ShortRecipeSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            author=obj, user__id=self.context['request'].user.id
        ).exists()
