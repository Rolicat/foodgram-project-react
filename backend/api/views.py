from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

from api.serializer import (
    CustomUsersSerializer, ProfileSerializer, RecipeListSerializer,
    IngredientSerializer, TagSerializer, CustomLoginSerializer,
    CustomLogoutSerializer, CustomUserCreate, RecipeSerializer,
    FavoriteSerializer, ShoppingCartSerializer, SubscriptionsSerializer,
)
from users.models import User, Follow
from app.models import Recipe, Ingredient, Tag, Favorite, ShoppingCart
from api.pagination import SubscribersPagination
from api.filters import RecipeFilter


class CustomLoginView(TokenObtainPairView):
    """View класс входа в приложение."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomLoginSerializer


class CustomLogoutView(TokenObtainPairView):
    """View класс выхода из приложения."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CustomLogoutSerializer


class CustomUsersViewSet(UserViewSet):
    """View-crud класс для пользователя(ей)."""
    queryset = User.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    search_fields = ('username', )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreate
        elif (self.action == 'me'
              and self.request
              and self.request.method == 'GET'
              ):
            return ProfileSerializer
        elif self.action in ('list', 'retrieve'):
            return CustomUsersSerializer
        elif self.action == 'subscriptions':
            return SubscriptionsSerializer
        return super().get_serializer_class()

    @action(methods=['get'], detail=False)
    def subscriptions(self, request):
        """Подписки пользователя."""
        queryset = User.objects.filter(following__user=request.user).all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SubscribesViewSet(viewsets.GenericViewSet,
                        viewsets.mixins.CreateModelMixin):
    queryset = User.objects.all()
    serializer_class = SubscriptionsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = SubscribersPagination

    def create(self, request, *args, **kwargs):
        """Подписаться на пользователя."""
        author = get_object_or_404(User, pk=kwargs['id'])
        queryset = Follow.objects.filter(user=request.user, author=author)
        if queryset.exists() or request.user == author:
            return Response(
                'Ошибка подписки',
                status=status.HTTP_400_BAD_REQUEST
                )
        Follow.objects.create(user=request.user, author=author)
        serializer = self.get_serializer(author)
        return Response(serializer.data)

    @action(methods=['delete'], detail=False)
    def delete(self, request, *args, **kwargs):
        """Отписаться от пользователя."""
        author = get_object_or_404(User, pk=kwargs['id'])
        queryset = Follow.objects.filter(user=request.user, author=author)
        if not queryset.exists():
            return Response(
                'Ошибка отписки',
                status=status.HTTP_400_BAD_REQUEST
                )
        queryset.delete()
        return Response(
            'Успешная отписка',
            status=status.HTTP_204_NO_CONTENT
            )


class RecipeViewSet(viewsets.ModelViewSet):
    """View-crud класс для рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeListSerializer
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    permission_classes = (permissions.AllowAny, )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if self.request.user != instance.author:
            return Response(
                'Не достаточно прав',
                status=status.HTTP_403_FORBIDDEN,
                )
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeListSerializer
        return RecipeSerializer

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        """Список покупок в формате pdf."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        return Response(shopping_cart)


class IngredientViewSet(viewsets.GenericViewSet,
                        viewsets.mixins.ListModelMixin,
                        viewsets.mixins.RetrieveModelMixin,
                        ):
    """View-crud класс для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    permission_classes = (permissions.AllowAny,)


class TagViewSet(viewsets.GenericViewSet,
                 viewsets.mixins.ListModelMixin,
                 viewsets.mixins.RetrieveModelMixin,):
    """View-crud класс для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class FavoriteViewSet(viewsets.GenericViewSet,
                      viewsets.mixins.CreateModelMixin,):
    """View для добавления и удаления из избранного."""
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs['id'])
        serializer.save(user=self.request.user, recipe=recipe)

    def create(self, request, *args, **kwargs):
        queryset = Favorite.objects.filter(
            user=request.user,
            recipe=get_object_or_404(pk=kwargs['id'])
        )
        if queryset.exists():
            return Response(
                'Рецепт уже в избранном',
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    @action(methods=('delete',), detail=False)
    def delete(self, request, *args, **kwargs):
        queryset = Favorite.objects.filter(
            recipe=kwargs['id'],
            user=request.user
        )
        if not queryset.exists():
            return Response(
                'Рецепта нет в списке избранного',
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(viewsets.GenericViewSet,
                          viewsets.mixins.CreateModelMixin,):
    """View для добавления и удаления из корзины."""
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        recipe = get_object_or_404(Recipe, pk=self.kwargs['id'])
        serializer.save(user=self.request.user, recipe=recipe)

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=kwargs['id'])
        queryset = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
            )
        if queryset.exists():
            return Response(
                'Рецепт уже в списке покупок',
                status=status.HTTP_400_BAD_REQUEST
                )
        return super().create(request, *args, **kwargs)

    @action(methods=('delete',), detail=False)
    def delete(self, request, *args, **kwargs):
        queryset = ShoppingCart.objects.filter(
            user=request.user,
            recipe=kwargs['id'],
            )
        if not queryset.exists():
            return Response(
                'Рецепта нет в списке покупок',
                status=status.HTTP_400_BAD_REQUEST
                )
        queryset.delete()
        return Response(
            'Рецепт удален из корзины',
            status=status.HTTP_204_NO_CONTENT
            )
