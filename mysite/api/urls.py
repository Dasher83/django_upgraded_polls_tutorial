from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from .views import QuestionViewSet, ChoiceViewSet, UserViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'question', QuestionViewSet, base_name='question')
router.register(r'choice', ChoiceViewSet, base_name='choice')
router.register(r'user', UserViewSet, base_name='user')

urlpatterns = [
    url(r'', include(router.urls)),
]
