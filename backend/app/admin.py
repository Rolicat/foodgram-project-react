from django.contrib import admin

from app.models import (
    Ingredient, Tag, Recipe, TagList, Composition,
    ShoppingCart, Favorite,
)
from app.constants import EMPTY_FIELD_VALUE


class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'name', 'text', 'cooking_time',
                    'pub_date', 'author',)
    list_editable = ('author', 'cooking_time',)
    search_fields = (
        'name', 'author__email', 'author__username'
    )
    list_filter = ('pub_date', 'cooking_time', 'tags')


class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)


class CompositionAdmin(admin.ModelAdmin):
    """Админка для ингредиентов в составе рецепта."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = (
        'recipe__name', 'recipe__author__email', 'recipe__author__username'
    )
    list_filter = ('recipe__tags',)


class TagListAdmin(admin.ModelAdmin):
    """Админка для тегов у рецепта."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'recipe', 'tag',)
    search_fields = (
        'recipe__name', 'recipe__author__email', 'recipe__author__username'
    )
    list_filter = ('tag',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка корзины покупок"""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'user', 'recipe')
    search_fields = (
        'recipe__name', 'recipe__author__email', 'recipe__author__username'
    )
    list_filter = ('recipe__tags',)


class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного"""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'user', 'recipe')
    search_fields = (
        'recipe__name', 'recipe__author__email', 'recipe__author__username'
    )
    list_filter = ('recipe__tags',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(TagList, TagListAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
