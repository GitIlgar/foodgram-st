from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField
from domain.models import User


class UserProfileSerializer(UserCreateSerializer):

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(subscriber=request.user).exists()
        return False


class CreateUserProfileSerializer(UserProfileSerializer):

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {"password": {"write_only": True}}


class UserProfileAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if representation['avatar'] and request:
            representation['avatar'] = request.build_absolute_uri(
                representation['avatar'])
        return representation

    def validate(self, data):
        avatar = data.get("avatar")
        if not avatar:
            raise serializers.ValidationError("Аватар не может быть пустым")

        return data
