from django.urls import include, path
from rest_framework import routers

from domain.views import (
    IngredientViewSet,
    RecipeViewSet,
    UserProfileViewSet,
    redirect_short_link
)

router = routers.DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("users", UserProfileViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
    path('s/<int:pk>', redirect_short_link, name='recipe-short-link'),

]
