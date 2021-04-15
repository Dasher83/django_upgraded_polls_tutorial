# Create your views here.
from rest_framework import viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from mysite import settings
from polls.models import Question, Choice, User, Answer
from .serializers import (
    QuestionSerializer,
    ChoiceSerializer,
    UserRetrieveSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    VoteSerializer,
    AnswerResultListSerializer,
)


class QuestionResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    http_method_names = ["post", "put", "delete"]
    pagination_class = QuestionResultsSetPagination

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        user = request.user
        question = self.get_object()
        data = {
            "user": user.id,
            "question": question.id,
            "choice": request.POST["choice"],
        }
        serializer = VoteSerializer(data=data)
        if serializer.is_valid():
            serializer.create(serializer.validated_data)
        else:
            if serializer.errors["non_field_errors"]:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        user = request.user
        question = self.get_object()
        answers = Answer.objects.filter(
            question__created_by=user.id, question=question.id
        )
        serializer = AnswerResultListSerializer(answers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
