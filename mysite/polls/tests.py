import datetime

from django.urls import reverse
from django.utils import timezone, html
from django.test import TestCase

from api.tests import create_choice
from mysite.testing_utils import create_basic_user
from .models import Question, Answer


def create_question(question_text, days, created_by):
    """
    Create a question with the given 'question_text' and published the given
    number of 'days' offset to now (negative for questions published in the
    past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(
        question_text=question_text, pub_date=time, created_by=created_by
    )


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available")
        self.assertQuerysetEqual(response.context["latest_question_list"], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the index page.
        """
        user = create_basic_user(return_plain_password=False)
        create_question(question_text="Past question.", days=-30, created_by=user)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"], ["<Question: Past question.>"]
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't
        displayed on the index page.
        """
        user = create_basic_user(return_plain_password=False)
        create_question(question_text="Future question.", days=30, created_by=user)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context["latest_question_list"], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist,
        only past questions are displayed.
        """
        user = create_basic_user(return_plain_password=False)
        create_question(question_text="Past question.", days=-30, created_by=user)
        create_question(question_text="Future question.", days=30, created_by=user)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"], ["<Question: Past question.>"]
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions
        """
        user = create_basic_user(return_plain_password=False)
        create_question(question_text="Past question 1.", days=-30, created_by=user)
        create_question(question_text="Past question 2.", days=-5, created_by=user)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerysetEqual(
            response.context["latest_question_list"],
            ["<Question: Past question 2.>", "<Question: Past question 1.>"],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with
        a pub_date in the future returns a 404 not found.
        """
        user = create_basic_user(return_plain_password=False)
        future_question = create_question(
            question_text="Future question.", days=5, created_by=user
        )
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date
        in the past displays the question's text.
        """
        user = create_basic_user(return_plain_password=False)
        past_question = create_question(
            question_text="Past Question.", days=-5, created_by=user
        )
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class QuestionVoteViewTests(TestCase):
    def test_vote_successfully(self):
        """
        Submit an Answer successfully.
        """
        user, user_password = create_basic_user()
        question = create_question(
            question_text="Some question.", days=5, created_by=user
        )
        choice = create_choice(choice_text="Some choice", question=question)
        url = reverse("polls:vote", args=(question.id,))
        data = {"choice": choice.id}
        self.client.force_login(user)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

    def test_vote_no_choice_selected(self):
        """
        Fail to submit an answer because no choice was selected
        """
        user, user_password = create_basic_user()
        question = create_question(
            question_text="Some question.", days=5, created_by=user
        )
        create_choice(choice_text="Some choice", question=question)
        url = reverse("polls:vote", args=(question.id,))
        data = {}
        self.client.force_login(user)
        response = self.client.post(url, data=data)
        self.assertContains(response, html.escape("You didn't select a choice."))

    def test_vote_anonymously(self):
        """
        Fail to submit an Answer because no authenticated user did so.
        """
        user, user_password = create_basic_user()
        question = create_question(
            question_text="Some question.", days=5, created_by=user
        )
        choice = create_choice(choice_text="Some choice", question=question)
        url = reverse("polls:vote", args=(question.id,))
        data = {"choice": choice.id}
        response = self.client.post(url, data=data)
        self.assertContains(response, "Answers cannot be anonymous.")

    def test_vote_already_voted(self):
        """
        Fail to submit an Answer because the given user already answered that question.
        """
        user, user_password = create_basic_user()
        question = create_question(
            question_text="Some question.", days=5, created_by=user
        )
        choice = create_choice(choice_text="Some choice", question=question)
        answer = Answer(question=question, choice=choice, user=user)
        answer.save()
        url = reverse("polls:vote", args=(question.id,))
        data = {"choice": choice.id}
        self.client.force_login(user)
        response = self.client.post(url, data=data)
        self.assertContains(response, "You already answered this question.")


class ResultsViewTests(TestCase):
    def test_get_results_successfully(self):
        """
        Get results without errors
        """
        user, user_password = create_basic_user()
        question = create_question(
            question_text="Some question", days=5, created_by=user
        )
        first_choice = create_choice(choice_text="The first choice", question=question)
        create_choice(choice_text="The second choice", question=question)
        answer = Answer(question=question, choice=first_choice, user=user)
        answer.save()
        url = reverse("polls:results", args=(question.id,))
        response = self.client.get(url)
        self.assertContains(response, "The first choice -- 1 vote")
        self.assertContains(response, "The second choice -- 0 votes")


class QuestionModelsTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() must return False
        for questions whose pub_date is in the future.
        """
        future_time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=future_time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose
        pub_date is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions
        whose pub_date is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)
