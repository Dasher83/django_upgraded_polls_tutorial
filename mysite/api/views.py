# Create your views here.
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response

from polls.models import Question, Choice, User
from .serializers import (
    QuestionSerializer,
    ChoiceSerializer,
    UserRetrieveSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    http_method_names = ["post", "put", "delete"]


class ChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = ChoiceSerializer
    queryset = Choice.objects.all()
    http_method_names = ["post", "put", "delete"]


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserRetrieveSerializer
    queryset = User.objects.all()
    serializer_action_classes = {
        "create": UserCreateSerializer,
        "update": UserUpdateSerializer,
    }
    http_method_names = ["post", "put", "delete"]

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk})
