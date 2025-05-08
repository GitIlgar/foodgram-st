from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from api.pagination import MainPagePagination
from api.permissions import IsAuthorOrReadOnly
from api.filters import IngredientFilter, RecipeFilter
from api.serializers import UserProfileAvatarSerializer, UserProfileSerializer

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    User
)
from .serializers import (
    CreateRecipeSerializer,
    FavoriteSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShortIngredientsSerializer,
    CreateSubscriptionSerializer,
    SubscriptionSerializer
)


def redirect_short_link(request, short_code):
    recipe = get_object_or_404(Recipe, pk=short_code)
    return redirect(recipe.get_absolute_url())  # Или другой URL рецепта


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = ShortIngredientsSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ("^name",)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = MainPagePagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return CreateRecipeSerializer

        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="favorite",
        url_name="favorite",
    )
    def favorite(self, request, pk):
        if request.method == "POST":
            return self.create_user_recipe_relation(
                request, pk, FavoriteSerializer
            )
        return self.delete_user_recipe_relation(
            request,
            pk,
            "favorites",
            Favorite.DoesNotExist,
            "Рецепт не в избранном.",
        )

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="shopping_cart",
        url_name="shopping_cart",
    )
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.create_user_recipe_relation(
                request, pk, ShoppingCartSerializer
            )
        return self.delete_user_recipe_relation(
            request,
            pk,
            "shopping_carts",
            ShoppingCart.DoesNotExist,
            "Рецепт не в списке покупок (корзине).",
        )

    def create_user_recipe_relation(self, request, pk, serializer_class):
        try:
            Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = serializer_class(
            data={
                "user": request.user.id,
                "recipe": pk,
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_user_recipe_relation(
        self,
        request,
        pk,
        related_name_for_user,
        does_not_exist_exception,
        does_not_exist_message,
    ):
        try:
            Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            getattr(request.user, related_name_for_user).get(
                user=request.user, recipe_id=pk
            ).delete()
        except does_not_exist_exception:
            return Response(
                does_not_exist_message,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
        url_name="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        shopping_cart_recipes = request.user.shopping_carts.all(
        ).values_list('recipe_id', flat=True)

        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe_id__in=shopping_cart_recipes)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit'
            )
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )

        return self.ingredients_to_txt(ingredients)

    @staticmethod
    def ingredients_to_txt(ingredients):
        shopping_list = "Список покупок:\n\n"
        shopping_list += "\n".join(
            f'• {ingredient['ingredient__name']} - {ingredient['total']} {
                ingredient['ingredient__measurement_unit']}'
            for ingredient in ingredients
        )

        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=("get",),
        permission_classes=(IsAuthenticatedOrReadOnly,),
        url_path="get-link",
        url_name="get-link",
    )
    def get_link(self, request, pk):
        instance = self.get_object()
        base_url = request.build_absolute_uri('/')[:-1]
        short_url = f"{base_url}/s/{instance.id}"

        return Response(data={"short-link": short_url})


class UserProfileViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = LimitOffsetPagination

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="me",
        url_name="me",
    )
    def me(self, request):
        serializer = UserProfileSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=("put", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="avatar",
        url_name="avatar",
    )
    def avatar(self, request, id):
        if request.method == "PUT":
            return self.create_avatar(request)
        return self.delete_avatar(request)

    def create_avatar(self, request):
        serializer = UserProfileAvatarSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(IsAuthenticated,),
        url_path="subscriptions",
        url_name="subscriptions",
    )
    def subscriptions(self, request):
        subscriptions = Subscription.objects.filter(subscriber=request.user)
        # Extract the authors (users being followed)
        authors = [sub.author for sub in subscriptions]

        # Paginate the authors
        pages = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="subscribe",
        url_name="subscribe",
    )
    def subscribe(self, request, id):
        if request.method == "POST":
            return self.create_subscription(request, id)
        return self.delete_subscription(request, id)

    def create_subscription(self, request, id):
        try:
            User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CreateSubscriptionSerializer(
            data={
                "subscriber": request.user.id,
                "author": id,
            },
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_subscription(self, request, id):
        try:
            author = User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = Subscription.objects.filter(
            subscriber=request.user.id, author=id
        )

        if not subscription.exists():
            return Response(
                f"Вы не подписаны на {author}",
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()

        return Response(
            f"Вы отписались от {author}", status=status.HTTP_204_NO_CONTENT
        )
