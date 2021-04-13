# Create your views here.
from rest_framework import viewsets

from polls.models import Question, Choice, User
from .serializers import (
    QuestionSerializer,
    ChoiceSerializer,
    UserRetrieveSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()


class ChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ChoiceSerializer
    queryset = Choice.objects.all()


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserRetrieveSerializer
    queryset = User.objects.all()
    serializer_action_classes = {
        "list": UserListSerializer,
        "create": UserCreateSerializer,
        "update": UserUpdateSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()
