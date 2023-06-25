from django.db import models
from users.models import User
from foodgram_backend.settings import VALIDATORS
from colorfield.fields import ColorField


class Ingredient(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name='Название',
        help_text='Название',
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='Единица измерения',
        help_text='Единица измерения',
    )

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name='Название тега',
        help_text='Название тега',
    )
    color = ColorField(
        verbose_name='цвет в hex формате',
        help_text='цвет в hex формате',
        default='#FFFFFF',
    )
    slug = models.SlugField(
        verbose_name='Сокращенное название',
        help_text='Сокращенное название',
    )

    class Meta:
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name}'


class Recipe(models.Model):
    ingredients = models.ManyToManyField(
        Ingredient,
        through='Composition',
        verbose_name='Ингредиенты',
        help_text='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagList',
        verbose_name='Теги',
        help_text='Теги',
    )
    image = models.ImageField(
        upload_to='recipies/images/',
        null=True,
        default=None,
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название',
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(VALIDATORS['more_than_one'],),
        verbose_name='Время приготовления (в минутах)',
        help_text='Время приготовления (в минутах)',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        help_text='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    pub_date = models.DateField(
        verbose_name='Дата публикации',
        help_text='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return f'{self.name} (время готовки:{self.cooking_time})'


class Composition(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='composition',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='composition',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        help_text='Количество',
        validators=(VALIDATORS['more_than_one'],),
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient',),
                name='unique_recipe_ingredient',
            ),
        )

    def __str__(self) -> str:
        return f'{self.recipe} {self.ingredient} {self.amount}'


class TagList(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='taglist',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag',),
                name='unique_recipe_tag',
            ),
        )

    def __str__(self) -> str:
        return f'{self.recipe} {self.tag}'


class ShoppingCart(models.Model):
    """Модель корзины покупок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_list',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_recipe_in_shopping_cart',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} хочет купить {self.recipe}.'


class Favorite(models.Model):
    """Модель избранных рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorited',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_recipe_favorite',
            ),
        )

    def __str__(self) -> str:
        return f'{self.user} хочет купить {self.recipe}.'
