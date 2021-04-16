from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import (
    QuestionViewSet,
    ChoiceViewSet,
    UserViewSet,
    CustomAuthToken,
    get_question_answers,
)

app_name = "api"

router = DefaultRouter()
router.register(r"question", QuestionViewSet, base_name="question")
router.register(r"choice", ChoiceViewSet, base_name="choice")
router.register(r"user", UserViewSet, base_name="user")

urlpatterns = [
    url(r"^login/$", CustomAuthToken.as_view(), name="login"),
    url(
        r"^question/(?P<question_id>[0-9]+)/results/$",
        get_question_answers,
        name="results",
    ),
    url(r"", include(router.urls)),
]
