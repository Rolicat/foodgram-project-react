from django.urls import include, path
from rest_framework import routers

from api.views import (
    CustomUsersViewSet, RecipeViewSet, IngredientViewSet, TagViewSet,
    CustomLoginView, CustomLogoutView, FavoriteViewSet, ShoppingCartViewSet,
    SubscribesViewSet,
)

router = routers.DefaultRouter()

router.register('users', CustomUsersViewSet)
router.register(r'users/(?P<id>\d+)/subscribe', SubscribesViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)
router.register('tags', TagViewSet)
router.register(
    r'recipes/(?P<id>\d+)/favorite',
    FavoriteViewSet,
)
router.register(
    r'recipes/(?P<id>\d+)/shopping_cart',
    ShoppingCartViewSet,
)
auth_patterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]
urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', include(auth_patterns)),
]
