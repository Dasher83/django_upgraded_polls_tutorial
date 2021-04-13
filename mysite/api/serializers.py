from rest_framework import serializers

from polls.models import Question, Choice, User


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class ChoiceSerializer(serializers.ModelSerializer):
    question = QuestionSerializer

    class Meta:
        model = Choice
        fields = "__all__"


class UserRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = (
            "password",
            "groups",
            "user_permissions",
            "date_joined",
            "last_login",
        )


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("id", "date_joined", "last_login")


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("id", "date_joined", "last_login")
