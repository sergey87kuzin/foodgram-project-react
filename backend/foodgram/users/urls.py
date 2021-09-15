from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router_user = SimpleRouter()
router_user.register('users', views.UserViewSet, basename='user')

user_patterns = [
    path('', include(router_user.urls)),
]

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(user_patterns)),
    path('users/<int:user_id>/subscribe/',
         views.subscription_view,
         name='subscribe'),
]
