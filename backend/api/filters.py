from django_filters.rest_framework import (
    FilterSet, CharFilter, BooleanFilter, ModelChoiceFilter,
    )

from app.models import Recipe
from users.models import User


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter()
    is_in_shopping_cart = BooleanFilter()
    author = ModelChoiceFilter(queryset=User.objects.all())
    tags = CharFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags',)
