from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router_v1 = SimpleRouter()
router_v1.register('recipes', views.RecipeViewSet, basename='recipe')
router_v1.register('tags', views.TagViewSet, basename='tag')
router_v1.register(
    'ingredients', views.IngredientViewSet, basename='ingredient'
)
api_v1_patterns = [
    path('', include(router_v1.urls)),
    path('recipes/<int:recipe_id>/shopping_cart/',
         views.cart_view,
         name='carts'),
    path('recipes/<int:recipe_id>/favorite/',
         views.favorite_view,
         name='favorites')
]

urlpatterns = [
    path('api/', include(api_v1_patterns)),
]
