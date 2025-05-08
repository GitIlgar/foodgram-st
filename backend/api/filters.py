from django_filters import rest_framework as filters
from django_filters.rest_framework import FilterSet
from domain.models import Recipe, Ingredient


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and hasattr(self.request, 'user'
                             ) and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value and hasattr(self.request, 'user'
                             ) and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart']


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ("name",)
