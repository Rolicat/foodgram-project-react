import io

from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet, TokenDestroyView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Sum

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from api.serializer import (
    CustomUsersSerializer, ProfileSerializer, RecipeListSerializer,
    IngredientSerializer, TagSerializer, CustomLoginSerializer,
    CustomUserCreate, RecipeSerializer,
    FavoriteSerializer, ShoppingCartSerializer, SubscriptionsSerializer,
)
from api.permission import IsAuthor
from api.filters import RecipeFilter
from users.models import User, Follow
from app.models import (
    Recipe, Ingredient, Tag, Favorite, ShoppingCart, Composition
)
from foodgram_backend.settings import PDFSettings, SHOPPING_CART_FILENAME


class CustomLoginView(TokenObtainPairView):
    """View класс входа в приложение."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomLoginSerializer


class CustomLogoutView(TokenDestroyView):
    """View класс выхода из приложения."""
    permission_classes = (permissions.IsAuthenticated,)


class CustomUsersViewSet(UserViewSet):
    """View-crud класс для пользователя(ей)."""
    queryset = User.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    search_fields = ('username', )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreate
        # Подставляем сериализатор профиля только, если
        # идет обращение к url 'users/me'
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

    @action(methods=('get',), detail=False)
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

    def create(self, request, *args, **kwargs):
        """Подписаться на пользователя."""
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка подписи',
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, pk=pk)
        queryset = Follow.objects.filter(user=request.user, author=author)
        if queryset.exists() or request.user == author:
            return Response(
                'Ошибка подписки',
                status=status.HTTP_400_BAD_REQUEST
            )
        Follow.objects.create(user=request.user, author=author)
        serializer = self.get_serializer(author)
        return Response(serializer.data)

    @action(methods=('delete',), detail=False)
    def delete(self, request, *args, **kwargs):
        """Отписаться от пользователя."""
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка отписки',
                status=status.HTTP_400_BAD_REQUEST
            )
        author = get_object_or_404(User, pk=pk)
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
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsAuthor)
    http_method_names = ('get', 'post', 'delete', 'patch')

    def perform_create(self, serializer):
        """Возвращаем полученный рецепт."""
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создаем рецепт с подменой сериализатора на возврат."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        serializer = RecipeListSerializer(
            instance=instance,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_update(self, serializer):
        """Возвращаем полученный рецепт."""
        return serializer.save()

    def update(self, request, *args, **kwargs):
        """Обновляем рецепт с подменой сериализатора на возврат."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_update(serializer)
        serializer = RecipeListSerializer(
            instance=instance,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def get_serializer_class(self):
        """Меняем сериализатор в зависимости от запроса."""
        if self.action in ('list', 'retrieve'):
            return RecipeListSerializer
        return RecipeSerializer

    @action(methods=('get',), detail=False)
    def download_shopping_cart(self, request):
        """Список покупок в формате pdf."""
        if request.user.is_anonymous:
            return Response(
                'Вы не авторизованы',
                status=status.HTTP_403_FORBIDDEN
            )
        shopping_cart = Composition.objects.filter(
            recipe__is_in_shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        buffer = io.BytesIO()
        pdfmetrics.registerFont(
            TTFont(PDFSettings.FONT_NAME, PDFSettings.FONT_SYSTEM_NAME)
        )
        pdf = canvas.Canvas(buffer)
        pdf.setFont(PDFSettings.FONT_NAME, PDFSettings.FONT_SIZE)
        pdf.drawString(
            PDFSettings.TITLE_X,
            PDFSettings.TITLE_Y,
            'СПИСОК ПОКУПОК'
        )
        y_position = PDFSettings.FIRST_STRING_Y
        for shopping_ingredient in shopping_cart:
            pdf.drawString(
                PDFSettings.FISRT_STRING_X,
                y_position,
                (f'{shopping_ingredient["ingredient__name"]} '
                 f'({shopping_ingredient["ingredient__measurement_unit"]})'
                 f' - [{shopping_ingredient["amount"]}]')
            )
            y_position -= PDFSettings.STRING_OFFSET
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename=SHOPPING_CART_FILENAME
        )


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
        pk = self.kwargs.get('id', None)
        if pk is None:
            raise ValidationError(
                'Ошибка создания рецепта',
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer.save(user=self.request.user, recipe=recipe)

    def create(self, request, *args, **kwargs):
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка поиска рецепта',
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = Favorite.objects.filter(
            user=request.user,
            recipe=get_object_or_404(Recipe, pk=pk)
        )
        if queryset.exists():
            return Response(
                'Рецепт уже в избранном',
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    @action(methods=('delete',), detail=False)
    def delete(self, request, *args, **kwargs):
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка поиска рецепта',
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = Favorite.objects.filter(
            recipe=pk,
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
        pk = self.kwargs.get('id', None)
        if pk is None:
            raise ValidationError(
                'Ошибка поиска рецепта',
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer.save(user=self.request.user, recipe=recipe)

    def create(self, request, *args, **kwargs):
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка поиска рецепта',
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, pk=pk)
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
        pk = kwargs.get('id', None)
        if pk is None:
            return Response(
                'Ошибка поиска рецепта',
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = ShoppingCart.objects.filter(
            user=request.user,
            recipe=pk,
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
