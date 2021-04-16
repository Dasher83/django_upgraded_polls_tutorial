import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.


class User(AbstractUser):
    @classmethod
    def create_user(
        cls, username, password, email=None, first_name=None, last_name=None
    ):
        if not username:
            raise ValueError("Users must have an username.")

        if not password:
            raise ValueError("Users must have a password.")

        user = User(
            username=username,
            email=cls.normalize_username(email),
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save()
        return user

    @classmethod
    def create_superuser(
        cls, username, password, email=None, first_name=None, last_name=None
    ):
        if not username:
            raise ValueError("Superusers must have an username.")

        if not password:
            raise ValueError("Superusers must have a password.")

        user = cls.create_user(username, email, password, first_name, last_name)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    was_published_recently.boolean = True
    was_published_recently.short_description = "Published recently?"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)

    def __str__(self):
        return self.choice_text

    def get_votes(self):
        raise NotImplementedError


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("question", "choice", "user")

    def __str__(self):
        representation = "Answer connects -> Question: %s. Choice: %s. User: %s."
        representation = representation % (
            self.question.question_text,
            self.choice.choice_text,
            self.user.username,
        )
        return representation
