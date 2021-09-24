from colorfield.fields import ColorField
from django.db import models
from users.models import User

from .validators import validator_amount, validator_time


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='название'
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='мера'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'

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
        null=True,
        verbose_name='картинка'
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
    text = models.TextField(verbose_name='текст рецепта')
    cooking_time = models.IntegerField(
        verbose_name='время приготовления',
        validators=[validator_time]
    )

    REQUIRED_FIELDS = [
        'author', 'name', 'image', 'ingredients',
        'tags', 'text', 'cooking_time'
    ]

    class Meta:
        ordering = ('-id',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'

    def __str__(self):
        return self.name

    def get_ingredients(self):
        results = []
        amounts = list(Amount.objects.filter(
            recipe__id=self.id).values_list(
                'ingredient__name', 'amount', 'ingredient__measurement_unit'))
        for amount in amounts:
            results.append(f'{amount[0]} {amount[1]} {amount[2]}')
        return ', '.join(results)

    def get_tags(self):
        tags = list(Tag.objects.filter(
            recipes__id=self.id).values_list('name', flat=True))
        return ', '.join(tags)


class Tag(models.Model):
    name = models.CharField(
        verbose_name='название',
        max_length=200
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='слаг'
    )
    colour = ColorField(default='#FF0000')

    class Meta:
        ordering = ('name',)
        verbose_name = 'тэг'
        verbose_name_plural = 'тэги'

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favorites', verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorites', verbose_name='рецепт'
    )

    class Meta:
        ordering = ('recipe__name',)
        verbose_name = 'избранное'
        verbose_name_plural = 'избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniq_favorite',
            )
        ]

    def __str__(self):
        return (
            f'любимое блюдо {self.user.username} - {self.recipe.name}'
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='carts', verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='carts', verbose_name='рецепт'
    )

    class Meta:
        ordering = ('recipe__name',)
        verbose_name = 'список'
        verbose_name_plural = 'списки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='uniq_cart',
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} собирается купить {self.recipe.name}'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='followers', verbose_name='пользователь'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='followings', verbose_name='автор'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='uniq_subscribe',
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} подписан на {self.author.username}'
        )


class Amount(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='quantities', verbose_name='рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        related_name='quantities', verbose_name='ингредиент'
    )
    amount = models.FloatField(
        verbose_name='количество',
        default=1,
        validators=[validator_amount]
    )

    class Meta:
        verbose_name = 'количество'
        verbose_name_plural = 'количества'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='uniq_amount',
            )
        ]

    def __str__(self):
        return str(self.amount)
