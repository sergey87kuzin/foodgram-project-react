
from django.contrib import admin
from django.contrib.auth.models import Group

from users.models import User

from .forms import AmountChangeForm, AmountCreationForm
from .models import (
    Amount, Favorite, Ingredient, Recipe, ShoppingCart, Subscription, Tag,
)


class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_staff')
    list_filter = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_staff')}),
        ('Personal info', {'fields': ('username', 'last_name', 'first_name')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'id')
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'name', 'image', 'get_ingredients', 'get_tags'
    )
    search_fields = ('name',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    empty_value_display = '-пусто-'


class AmountAdmin(admin.ModelAdmin):
    form = AmountChangeForm
    add_form = AmountCreationForm

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe',)
    list_filter = ('recipe',)
    empty_value_display = '-пусто-'


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)


class ShoppindCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = '-пусто-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user',)
    list_filter = ('user',)
    empty_value_display = '-пусто-'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Amount, AmountAdmin)
admin.site.register(ShoppingCart, ShoppindCartAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
