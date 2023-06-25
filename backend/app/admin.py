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
    search_fields = ('text',)
    list_editable = ('author', 'cooking_time',)
    list_filter = ('pub_date', 'cooking_time',)


class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)


class CompositionAdmin(admin.ModelAdmin):
    """Админка для ингредиентов в составе рецепта."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe',)


class TagListAdmin(admin.ModelAdmin):
    """Админка для тегов у рецепта."""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'recipe', 'tag',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка корзины покупок"""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'user', 'recipe')


class FavoriteAdmin(admin.ModelAdmin):
    """Админка избранного"""
    empty_value_display = EMPTY_FIELD_VALUE
    list_display = ('pk', 'user', 'recipe')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(TagList, TagListAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
