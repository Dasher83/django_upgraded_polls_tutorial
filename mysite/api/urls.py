from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import QuestionViewSet, ChoiceViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'question', QuestionViewSet, base_name='question')
router.register(r'choice', ChoiceViewSet, base_name='choice')

urlpatterns = [
    url(r'', include(router.urls)),
]
