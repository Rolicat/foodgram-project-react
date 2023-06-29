from django_filters.rest_framework import (
    FilterSet, CharFilter, BooleanFilter, ModelChoiceFilter,
)

from app.models import Recipe
from users.models import User


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method='filter_boolean')
    is_in_shopping_cart = BooleanFilter(method='filter_boolean')
    author = ModelChoiceFilter(queryset=User.objects.all())
    tags = CharFilter(field_name='tags__slug')

    def filter_boolean(self, queryset, name, value):
        """Т.к. нам приходит 0 или 1, мы меняем на true или false."""
        if value:
            return queryset.filter(
                **{'__'.join((name, 'user')): self.request.user}
            )
        return queryset

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags',)
