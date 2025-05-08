from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from api.serializers import UserProfileSerializer

from .constants import INGREDIENT_MIN_AMOUNT_IN_RECIPE
from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Subscription
)


class SubscriptionSerializer(UserProfileSerializer):
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    recipes_count = serializers.SerializerMethodField(
        method_name="get_recipes_count")

    class Meta(UserProfileSerializer.Meta):
        fields = ("recipes",
                  "recipes_count",
                  ) + UserProfileSerializer.Meta.fields

    def get_recipes(self, obj):
        request = self.context.get('request')
        author = obj
        recipes = author.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('author', 'subscriber')
        extra_kwargs = {
            'author': {'write_only': True},
            'subscriber': {'write_only': True},
        }

    def validate(self, data):
        if data['subscriber'] == data['author']:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя!"
            )

        if Subscription.objects.filter(
            subscriber=data['subscriber'],
            author=data['author']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора')

        return data

    def to_representation(self, instance):
        serializer = SubscriptionSerializer(
            instance.author,
            context=self.context
        )
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit", "amount")


class ShortIngredientsSerializer(serializers.ModelSerializer):
    """Serialize ingredients without IngredientInRecipe fields."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    measurement_unit = serializers.CharField()

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    ingredients = IngredientSerializer(
        source="ingredients_in_recipe", many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        return (
            request is not None
            and request.user.is_authenticated
            and request.user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.shopping_carts.filter(user=request.user).exists()
        return False


class CreateShortIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ("id", "amount")

    def validate_id(self, ingredient_id):
        if not Ingredient.objects.filter(id=ingredient_id).exists():
            raise serializers.ValidationError(
                f"Ингредиента с id {ingredient_id} не существует."
            )

        return ingredient_id

    def validate_amount(self, value):
        if value < INGREDIENT_MIN_AMOUNT_IN_RECIPE:
            raise serializers.ValidationError(
                "Количество ингредиента должно быть больше {}!".format(
                    INGREDIENT_MIN_AMOUNT_IN_RECIPE - 1
                )
            )
        return value


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = CreateShortIngredientsSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "name",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={"request": self.context.get("request")}
        )
        return serializer.data

    def validate(self, data):
        ingredients = data.get("ingredients")
        if not data.get('image'):
            raise serializers.ValidationError({
                "image": ["Обязательное поле."]
            })
        if not ingredients:
            raise serializers.ValidationError(
                "Список ингредиентов не может быть пустым!"
            )

        ingredients_ids = [el["id"] for el in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                "Ингредиенты должны быть уникальными!"
            )

        return data

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")

        user = self.context.get("request").user
        recipe = Recipe.objects.create(**validated_data, author=user)
        self.create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        IngredientInRecipe.objects.filter(recipe=instance).delete()

        self.create_ingredients(validated_data.pop("ingredients"), instance)

        return super().update(instance, validated_data)

    def create_ingredients(self, ingredients, recipe):
        IngredientInRecipe.objects.bulk_create(
            IngredientInRecipe(
                ingredient_id=element["id"],
                recipe=recipe,
                amount=element["amount"]
            )
            for element in ingredients
        )


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserRecipeRelationSerializer(serializers.Serializer):

    class Meta:
        fields = ("user", "recipe")

    def to_representation(self, instance):
        serializer = ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        )
        return serializer.data

    def validate(self, data, related_name):
        user = data.get("user")
        recipe = data.get("recipe")

        if getattr(user, related_name).filter(recipe__id=recipe.id).exists():
            raise serializers.ValidationError(
                f"{related_name} пользователя {user.username} "
                f"уже содержит рецепт {recipe.name}."
            )

        return data


class FavoriteSerializer(
    UserRecipeRelationSerializer, serializers.ModelSerializer
):

    class Meta(UserRecipeRelationSerializer.Meta):
        model = Favorite

    def validate(self, data):
        return super().validate(data, "favorites")


class ShoppingCartSerializer(
    UserRecipeRelationSerializer, serializers.ModelSerializer
):

    class Meta(UserRecipeRelationSerializer.Meta):
        model = ShoppingCart

    def validate(self, data):
        return super().validate(data, "shopping_carts")
