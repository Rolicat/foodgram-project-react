import base64

from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import (
    UserSerializer, UserCreateSerializer
)

from users.validators import UsernameRegexValidator
from users.models import User
from app.models import (
    Recipe, Ingredient, Tag,
    Favorite, ShoppingCart, TagList,
    Composition,
)
from foodgram_backend.settings import MIN_AMOUNT, MIN_COOKING_TIME


class CustomUserCreate(UserCreateSerializer):
    """Сериализатор создания пользователя."""
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username',
            'email', 'password', 'id',
        )


class CustomLoginSerializer(TokenObtainPairSerializer):
    """
    Сериализатор входа в приложение.
    Модель пользователя модифицирована для входа по email.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        data = {'auth_token': data['access']}
        return data


class CustomUsersSerializer(UserSerializer):
    """Сериализатор для пользователей."""
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=(
            UniqueValidator(queryset=User.objects.all()),
            UsernameRegexValidator(),
        )
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed',
        )
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        """Получаем информацию о подписи на пользователя."""
        if self.context['request'].user.is_anonymous:
            return False
        return obj.following.filter(user=self.context['request'].user).exists()


class ProfileSerializer(CustomUsersSerializer):
    """Сериализатор для профиля зарегистрированного пользователя."""

    def get_is_subscribed(self, obj):
        """
        У текущего профиля всегда нет подписи на самого себя.
        Всегда возвращаем False, чтобы не просчитывать наличие подписки.
        Этот сериализатор используется для @action 'me'.
        """
        return False


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class CompositionSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов для рецепта."""
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = Composition
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тэгов."""
    name = serializers.CharField(read_only=True)
    color = serializers.CharField(read_only=True)
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class Base64ImageField(serializers.ImageField):
    """Функция преобразования из шифрованной строки в картинку."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True,
    )

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image',
                            'cooking_time', 'user', 'recipe',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины покупок."""

    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True,
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image',
                            'cooking_time', 'user', 'recipe',)


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов list и retreive."""
    image = Base64ImageField(required=False, allow_null=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True, required=True)
    author = CustomUsersSerializer(read_only=True)
    ingredients = CompositionSerializer(
        source='composition',
        many=True,
        required=True,
    )

    def get_is_favorited(self, recipe):
        """Рецепт в избранном или нет."""
        if self.context['request'].user.is_anonymous:
            return False
        user = self.context['request'].user
        return recipe.is_favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        """Рецепт в корзине или нет."""
        if self.context['request'].user.is_anonymous:
            return False
        user = self.context['request'].user
        return recipe.is_in_shopping_cart.filter(user=user).exists()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('author',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        required=True,
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(required=True),
        required=True,
        write_only=True,
    )

    def validate_cooking_time(self, cooking_time: int):
        if int(cooking_time) < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время готовки не может быть менее {MIN_COOKING_TIME} минуты'
            )
        return cooking_time

    def validate_ingredients(self, ingredients: list):
        """Проверим количество ингредиентов и их повторяемость."""
        if not isinstance(ingredients, list):
            raise serializers.ValidationError(
                'Не корректное значение списка ингредиентов'
            )
        if not len(ingredients):
            raise serializers.ValidationError(
                'Не указан ни один ингредиент для рецепта'
            )
        reply_check = {}
        for ingredient in ingredients:
            if ingredient['id'] in reply_check:
                raise serializers.ValidationError(
                    'В рецепте есть повторяющиеся ингредиенты'
                )
            reply_check[ingredient['id']] = ingredient['amount']
            if int(ingredient['amount']) < MIN_AMOUNT:
                raise serializers.ValidationError(
                    f'Количество ингредиентов не может '
                    f'быть меньше {MIN_AMOUNT}'
                )
        return ingredients

    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        TagList.objects.bulk_create(
            [TagList(
                recipe=recipe,
                tag=tag
            ) for tag in tags]
        )
        Composition.objects.bulk_create(
            [Composition(
                recipe=recipe,
                ingredient=get_object_or_404(
                    Ingredient,
                    pk=ingredient_info['id']
                ),
                amount=ingredient_info['amount'],
            ) for ingredient_info in ingredients]
        )
        return recipe

    def update(self, recipe, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        Recipe.objects.filter(pk=recipe.id).update(**validated_data)
        # Сперва удалим все привязки тегов
        TagList.objects.filter(recipe=recipe).delete()
        # Добавим теги вновь
        TagList.objects.bulk_create(
            [TagList(
                recipe=recipe,
                tag=tag
            ) for tag in tags]
        )
        # Сперва удалим все привязки ингредиентов
        Composition.objects.filter(recipe=recipe).delete()
        # Добавим ингредиенты вновь
        Composition.objects.bulk_create(
            [Composition(
                recipe=recipe,
                ingredient=get_object_or_404(
                    Ingredient,
                    pk=ingredient_info['id']
                ),
                amount=ingredient_info['amount'],
            ) for ingredient_info in ingredients]
        )
        return recipe

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('author',)


class SmallRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionsSerializer(CustomUsersSerializer):
    """Сериализатор для списка подписчиков."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        """Рецепты с лимитированием."""
        limit = self.context['request'].query_params.get('recipes_limit', None)
        queryset = Recipe.objects.filter(author=obj).all()
        if limit:
            queryset = queryset[:int(limit)]
        return SmallRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        """Количество рецептов."""
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed',
            'recipes', 'recipes_count',
        )
