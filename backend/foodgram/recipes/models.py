from colorfield.fields import ColorField
from django.db import models

from users.models import User

from .validators import validator_amount, validator_time


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор рецепта',
        related_name='recipes'
    )
    name = models.CharField(
        unique=True,
        max_length=200,
        verbose_name='название рецепта'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='компоненты',
        related_name='recipes',
        through='Amount'
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        verbose_name='теги',
        related_name='recipes'
    )
    text = models.TextField()
    cooking_time = models.IntegerField(validators=[validator_time])

    REQUIRED_FIELDS = [
        'author', 'name', 'image', 'ingredients',
        'tags', 'text', 'cooking_time'
    ]

    class Meta:
        ordering = ('-id',)

    def __str__(self):
        return self.name

    def ingredient_set(self):
        return Amount.objects.filter(recipe__id=self.id)

    def get_author(self):
        return self.author

    def get_ingredients(self):
        amounts = Amount.objects.select_related(
            'ingredient').filter(recipe__id=self.id)
        return ', '.join(
            [amount.ingredient.name + str(amount.amount) +
             amount.ingredient.measurement_unit
             for amount in amounts]
        )

    def get_tags(self):
        tags = Tag.objects.filter(recipes__id=self.id)
        return ', '.join(str(tag.name) for tag in tags)


class Tag(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Slug'
    )
    colour = ColorField(default='#FF0000')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites'
    )

    class Meta:
        ordering = ('recipe__name',)

    def __str__(self):
        return (
            f'любимое блюдо {self.user.username} - {self.recipe.name}'
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='carts'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='carts'
    )

    class Meta:
        ordering = ('recipe__name',)

    def __str__(self):
        return (
            f'{self.user.username} собирается купить {self.recipe.name}'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followings'
    )

    def __str__(self):
        return (
            f'{self.user.username} подписан на {self.author.username}'
        )

    def subscribe_set(self):
        return Recipe.objects.filter(
            author=self.author
        )


class Amount(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='quantities'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='quantities'
    )
    amount = models.FloatField(
        verbose_name='количество',
        default=1,
        validators=[validator_amount]
    )

    def __str__(self):
        return str(self.amount)

    def recipe_name(self):
        return self.recipe.name

    def recipe_unit(self):
        return self.recipe.measurement_unit
