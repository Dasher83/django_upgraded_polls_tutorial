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


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("date_joined", "last_login")

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(user.password)
        user.is_active = True
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ("id", "date_joined", "last_login")

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        instance.set_password(instance.password)
        instance.save()
        return instance
