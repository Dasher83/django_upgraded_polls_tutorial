import datetime
import json
from copy import deepcopy
from random import randint

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail

from mysite import settings
from mysite.testing_utils import create_basic_user
from polls.models import Question, Choice, User, Answer


class ApiTestCase(TestCase):
    def login(self, username, password):
        login_url = "/api/polls/login/"
        login_data = {"username": username, "password": password}
        response = self.client.post(login_url, data=login_data)
        self.assertEqual(response.status_code, 200)
        login_response = response.data
        token = login_response["token"]
        return token

    def post(self, target_url, token, data, expected_response_status=200):
        auth_headers = dict()
        if token:
            auth_headers["HTTP_AUTHORIZATION"] = "Token %s" % token
        response = self.client.post(target_url, data=data, **auth_headers)
        self.assertEqual(expected_response_status, response.status_code)
        return response

    def put(self, target_url, token, data, expected_response_status=200):
        auth_headers = dict()
        if token:
            auth_headers["HTTP_AUTHORIZATION"] = "Token %s" % token
        response = self.client.put(
            target_url,
            data=json.dumps(data),
            content_type="application/json",
            **auth_headers
        )
        self.assertEqual(expected_response_status, response.status_code)
        return response

    def delete(self, target_url, token, expected_response_status=200):
        auth_headers = dict()
        if token:
            auth_headers["HTTP_AUTHORIZATION"] = "Token %s" % token
        response = self.client.delete(target_url, **auth_headers)
        self.assertEqual(expected_response_status, response.status_code)
        return response

    def get(self, target_url, token, expected_response_status=200):
        # Todo: Add query params management as soon as they are needed in a test
        auth_headers = dict()
        if token:
            auth_headers["HTTP_AUTHORIZATION"] = "Token %s" % token
        response = self.client.get(target_url, **auth_headers)
        self.assertEqual(expected_response_status, response.status_code)
        return response


def create_question(question_text, days, created_by):
    """
    Create a question with the given 'question_text' and published the given
    number of 'days' offset to now (negative for questions published in the
    past, positive for questions that have yet to be published).
    """
    time = timezone.localtime(timezone.now()) + datetime.timedelta(days=days)
    return Question.objects.create(
        question_text=question_text, pub_date=time, created_by=created_by
    )


def create_choice(choice_text, question):
    """
    Create a choice with the given 'choice_text' related to the given 'question', created_by a certian user
    """
    return Choice.objects.create(choice_text=choice_text, question=question)


def create_answer(question, choice, user):
    """
    Create an answer for the question with the choice given by the respondent user
    """
    return Answer.objects.create(question=question, choice=choice, user=user)


def entity_to_dict(entity_instance, allowed_fields, fields=None):
    """
    Place Holder
    :param entity_instance:
    :param allowed_fields:
    :param fields:
    :return:
    """
    representation = {
        field: getattr(entity_instance, field) for field in allowed_fields
    }
    if fields:
        representation = {
            field: representation[field] for field in fields if field in allowed_fields
        }
    return representation


def get_allowed_fields_of_entity(entity_name):
    """
    Place holder
    :param entity_name:
    :return:
    """
    entities_allowed_fields_map = {
        "Question": {"id", "question_text", "pub_date"},
        "Choice": {"id", "choice_text", "question"},
        "User": {
            "id",
            "password",
            "last_login",
            "is_superuser",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "groups",
            "user_permissions",
        },
    }
    return entities_allowed_fields_map[entity_name]


class QuestionPostViewTests(ApiTestCase):
    def test_post_question_successfully(self):
        """
        Create a new question without errors
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/"
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=question_data, expected_response_status=201
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_post_question_bad_format_pub_date(self):
        """
        Fail to create a new question because
        the format of the publication date is not correct
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        incorrect_values = ("", "incorrect_date_format", 1)
        for incorrect_value in incorrect_values:
            question_data = {
                "question_text": "What is your favorite series",
                "created_by": user.id,
                "pub_date": incorrect_value,
            }
            target_url = "/api/polls/question/"
            token = self.login(user.username, user_password)
            response = self.post(
                target_url, token, data=question_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {
                "pub_date": [
                    "Datetime has wrong format. Use one of these formats "
                    "instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ]
            }
            self.assertEqual(expected_error, response_error)

    def test_post_question_exclude_required_field(self):
        """
        Fail to create a new question because some or all required fields were not included
        """
        required_fields = {"question_text", "pub_date", "created_by"}
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        base_question_data = {
            "question_text": "some question",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/"
        token = self.login(user.username, user_password)
        for required_field in required_fields:
            question_data = {
                key: value
                for (key, value) in base_question_data.items()
                if key != required_field
            }
            response = self.post(
                target_url, token, data=question_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)
        response = self.post(target_url, token, data={}, expected_response_status=400)
        response_error = json.loads(response.content)
        expected_error = {
            required_field: ["This field is required."]
            for required_field in required_fields
        }
        self.assertEqual(expected_error, response_error)

    def test_post_question_blank_question_text(self):
        """
        Fail to create a new question because question_text was blank
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_data = {
            "question_text": "",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/"
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)

    def test_post_question_null_created_by(self):
        """
        Fail to create a new question because question_text was blank
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_data = {
            "question_text": "some question",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": "",
        }
        target_url = "/api/polls/question/"
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"created_by": ["This field may not be null."]}
        self.assertEqual(expected_error, response_error)


class QuestionPutViewTests(ApiTestCase):
    def test_put_question_successfully(self):
        """
        Update a new question without errors
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        question_new_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=question_new_data, expected_response_status=200
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_new_data)), response_data)

    def test_put_question_bad_format_pub_date(self):
        """
        Fail to update a new question because
        the format of the publication date is not correct
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        incorrect_values = ("", "incorrect_date_format", 1)
        for incorrect_value in incorrect_values:
            question_new_data = {
                "question_text": "What is your favorite series",
                "pub_date": incorrect_value,
                "created_by": user.id,
            }
            target_url = "/api/polls/question/%s/"
            target_url = target_url % question_instance.id
            token = self.login(user.username, user_password)
            response = self.put(
                target_url, token, data=question_new_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {
                "pub_date": [
                    "Datetime has wrong format. Use one of these formats "
                    "instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]."
                ]
            }
            self.assertEqual(expected_error, response_error)

    def test_put_question_exclude_required_field(self):
        """
        Fail to update an existing question because some or all required fields were not included
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        required_fields = {"question_text", "pub_date", "created_by"}
        base_new_question_data = {
            "question_text": "some question",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        for required_field in required_fields:
            question_data = {
                key: value
                for (key, value) in base_new_question_data.items()
                if key != required_field
            }
            response = self.put(
                target_url, token, data=question_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)
        response = self.put(target_url, token, data={}, expected_response_status=400)
        response_error = json.loads(response.content)
        expected_error = {
            required_field: ["This field is required."]
            for required_field in required_fields
        }
        self.assertEqual(expected_error, response_error)

    def test_put_question_blank_question_text(self):
        """
        Fail to update an existing question because question_text were blank
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        question_data = {
            "question_text": "",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": user.id,
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)

    def test_put_question_null_non_nullable_field(self):
        """
        Fail to update an existing question because created_by was sent null
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        question_data = {
            "question_text": "some question",
            "pub_date": "2021-04-08T09:27:35-03:00",
            "created_by": "",
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"created_by": ["This field may not be null."]}
        self.assertEqual(expected_error, response_error)


class QuestionVoteViewTests(ApiTestCase):
    def test_vote_successfully(self):
        """
        Submit an answer using an existing choice for a given question successfully
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=user,
        )
        target_url = "/api/polls/question/%s/vote/"
        target_url = target_url % question_instance.id
        selected_choice_instance = create_choice(
            choice_text="Red pill", question=question_instance
        )
        create_choice(choice_text="Blue pill", question=question_instance)
        vote_data = {"choice": selected_choice_instance.id}
        token = self.login(user.username, user_password)
        self.post(target_url, token, data=vote_data, expected_response_status=201)

    def test_vote_nonexistent_question(self):
        """
        Submit an answer using an existing choice for a question that does not exist
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=user,
        )
        target_url = "/api/polls/question/%s/vote/"
        nonexistent_id = question_instance.id + 1
        target_url = target_url % nonexistent_id
        token = self.login(user.username, user_password)
        response = self.post(target_url, token, data={}, expected_response_status=404)
        expected_error = {"detail": ErrorDetail(string="Not found.", code="not_found")}
        response_error = response.data
        self.assertEqual(expected_error, response_error)

    def test_vote_nonexistent_choice(self):
        """
        Submit an answer for a question using a choice that does not exist
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=user,
        )
        target_url = "/api/polls/question/%s/vote/"
        selected_choice_instance = create_choice(
            choice_text="Red pill", question=question_instance
        )
        nonexistent_choice_id = selected_choice_instance.id + 1
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        vote_data = {"choice": nonexistent_choice_id}
        response = self.post(
            target_url, token, data=vote_data, expected_response_status=400
        )
        expected_error = {
            "choice": [
                ErrorDetail(
                    string='Invalid pk "%s" - object does not exist.'
                    % nonexistent_choice_id,
                    code="does_not_exist",
                )
            ]
        }
        response_error = response.data
        self.assertEqual(expected_error, response_error)

    def test_vote_not_numeric_choice_id(self):
        """
        Submit an answer for a question using a choice id that is not a number
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=user,
        )
        target_url = "/api/polls/question/%s/vote/"
        non_numeric_choice_id = "x"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        vote_data = {"choice": non_numeric_choice_id}
        response = self.post(
            target_url, token, data=vote_data, expected_response_status=400
        )
        expected_error = {
            "choice": [
                ErrorDetail(
                    string="Incorrect type. Expected pk value, received str.",
                    code="incorrect_type",
                )
            ]
        }
        response_error = response.data
        self.assertEqual(expected_error, response_error)

    def test_vote_already_answered_question(self):
        """
        Submit an answer for a question that the requester already answered
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=user,
        )
        target_url = "/api/polls/question/%s/vote/"
        target_url = target_url % question_instance.id
        selected_choice_instance = create_choice(
            choice_text="Red pill", question=question_instance
        )
        create_choice(choice_text="Blue pill", question=question_instance)
        vote_data = {"choice": selected_choice_instance.id}
        token = self.login(user.username, user_password)
        create_answer(
            question=question_instance, choice=selected_choice_instance, user=user
        )
        response = self.post(
            target_url, token, data=vote_data, expected_response_status=409
        )
        expected_error = {
            "non_field_errors": [
                "The fields question, choice, user must make a unique set."
            ]
        }
        response_error = response.data
        self.assertEqual(expected_error, response_error)


class QuestionDeleteViewTests(ApiTestCase):
    def test_delete_question_successfully(self):
        """
        Delete an existing question without errors
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.delete(target_url, token, expected_response_status=204)
        expected_data = b""
        self.assertEqual(expected_data, response.content)

    def test_delete_question_non_existent(self):
        """
        Delete an existing question unsuccessfully since
        it does not exist any Question with the requested id
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        target_url = "/api/polls/question/%s/"
        non_existent_id = question_instance.id + 1
        target_url = target_url % non_existent_id
        token = self.login(user.username, user_password)
        response = self.delete(target_url, token, expected_response_status=404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


def create_test_data(question):
    """
    Creates some test answers for the given question
    :return: the expected data correspondent to the test data created
    """
    # Todo: should automate this with Faker like suggested by reviewers
    red_pill_choice_instance = create_choice(choice_text="Red pill", question=question)
    blue_pill_choice_instance = create_choice(
        choice_text="Blue pill", question=question
    )
    expected_data = []
    base_user_data = {
        "username": "test_%s",
        "password": "1234",
        "email": "test_%s@matrix.com",
        "first_name": "Test %s",
        "last_name": "Anderson",
    }
    data_volume = settings.REST_FRAMEWORK["PAGE_SIZE"]
    data_volume = data_volume + randint(1, settings.REST_FRAMEWORK["PAGE_SIZE"])
    for index in range(0, data_volume + 1):
        user_data = deepcopy(base_user_data)
        user_data.update(
            {
                "username": "test_%s" % index,
                "email": "test_%s@matrix.com" % index,
                "first_name": "Test %s" % index,
            }
        )
        user_instance = User.create_user(**user_data)
        choice = (
            red_pill_choice_instance
            if randint(1, 2) == 1
            else blue_pill_choice_instance
        )
        create_answer(question=question, user=user_instance, choice=choice)
        expected_data_item = {
            "user": {"id": user_instance.id, "username": user_instance.username},
            "choice": {"id": choice.id, "choice_text": choice.choice_text},
        }
        expected_data.append(expected_data_item)

    return expected_data


class QuestionAnswersViewTests(ApiTestCase):
    def test_get_question_answers_successfully(self):
        """
        Get Answers successfully for a question a certain user created
        """
        enquirer_plain_password = "1234"
        enquirer_user_data = {
            "username": "morpheus",
            "password": enquirer_plain_password,
            "email": "morpheus@matrix.com",
            "first_name": "Morpheus",
            "last_name": "Unknown",
        }
        enquirer_user = User.create_user(**enquirer_user_data)
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=enquirer_user,
        )
        expected_data = create_test_data(question_instance)
        target_url = "/api/polls/question/%s/results/"
        target_url = target_url % question_instance.id
        token = self.login(enquirer_user.username, enquirer_plain_password)
        response = self.get(target_url, token, expected_response_status=200)
        response_data = response.data
        self.assertEqual(expected_data, response_data)

    def tests_get_question_answers_no_answers(self):
        """
        Get Answers for a question nobody answer
        """
        user, user_password = create_basic_user()
        question_instance = create_question(
            question_text="Some question", days=30, created_by=user
        )
        expected_data = []
        target_url = "/api/polls/question/%s/results/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.get(target_url, token, expected_response_status=200)
        response_data = response.data
        self.assertEqual(expected_data, response_data)

    def tests_get_question_answers_non_enquirer_request(self):
        """
        Get Answers for a question that the requester did not create
        """
        enquirer_plain_password = "1234"
        enquirer_user_data = {
            "username": "morpheus",
            "password": enquirer_plain_password,
            "email": "morpheus@matrix.com",
            "first_name": "Morpheus",
            "last_name": "Unknown",
        }
        enquirer_user = User.create_user(**enquirer_user_data)
        question_instance = create_question(
            question_text="Do you want to know what is the Matrix?",
            days=30,
            created_by=enquirer_user,
        )
        user, user_password = create_basic_user()
        target_url = "/api/polls/question/%s/results/"
        target_url = target_url % question_instance.id
        token = self.login(user.username, user_password)
        response = self.get(target_url, token, expected_response_status=403)
        expected_error = "Only the creator of a question can obtain its answers"
        response_error = response.data
        self.assertEqual(expected_error, response_error)

    def tests_get_question_answers_nonexistent_question(self):
        """
        Get Answers for a question that it doesn't exist
        """
        user, user_password = create_basic_user()
        question_instance = create_question(
            question_text="Some question", days=30, created_by=user
        )
        nonexistent_id = question_instance.id + 1
        target_url = "/api/polls/question/%s/results/"
        target_url = target_url % nonexistent_id
        token = self.login(user.username, user_password)
        response = self.get(target_url, token, expected_response_status=404)
        expected_error = {"detail": ErrorDetail(string="Not found.", code="not_found")}
        response_error = response.data
        self.assertEqual(expected_error, response_error)


class ChoiceDeleteViewTests(ApiTestCase):
    def test_delete_choice_successfully(self):
        """
        Delete an existing choice without errors
        """
        user, user_password = create_basic_user()
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice.", question=question_instance
        )
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        token = self.login(user.username, user_password)
        response = self.delete(target_url, token, expected_response_status=204)
        expected_data = b""
        self.assertEqual(expected_data, response.content)

    def test_delete_choice_non_existent(self):
        """
        Delete an existing choice unsuccessfully since
        it does not exist any choice with the requested id
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice.", question=question_instance
        )
        target_url = "/api/polls/choice/%s/"
        non_existent_id = choice_instance.id + 1
        target_url = target_url % non_existent_id
        token = self.login(user.username, user_password)
        response = self.delete(target_url, token, expected_response_status=404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class ChoicePostViewTests(ApiTestCase):
    def test_post_choice_successfully(self):
        """
        Create a new choice without errors
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_data = {
            "choice_text": "Some choice",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/"
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=201
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(choice_data)), response_data)

    def test_post_choice_exclude_required_fields(self):
        """
        Fail to create a new choice because a required field is not included
        """
        required_fields = ("choice_text", "question")
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        original_choice_data = {
            "choice_text": "Some choice",
            "question": question_instance.id,
        }
        for required_field in required_fields:
            choice_data = {
                key: value
                for (key, value) in original_choice_data.items()
                if key is not required_field
            }
            target_url = "/api/polls/choice/"
            token = self.login(user.username, user_password)
            response = self.post(
                target_url, token, data=choice_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)

    def test_post_choice_blank_choice_text(self):
        """
        Fail to create a new choice because choice_text is blank
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_data = {"choice_text": "", "question": question_instance.id}
        target_url = "/api/polls/choice/"
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"choice_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)

    def test_post_choice_null_question(self):
        """
        Fail to create a new choice because question is null
        """
        choice_data = {"choice_text": "Some choice", "question": ""}
        target_url = "/api/polls/choice/"
        user, user_password = create_basic_user()
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question": ["This field may not be null."]}
        self.assertEqual(expected_error, response_error)

    def test_post_choice_not_question_pk(self):
        """
        Fail to create a new choice because question is not a numeric id
        """
        choice_data = {
            "choice_text": "Some choice",
            "question": "some question",
        }
        target_url = "/api/polls/choice/"
        user, user_password = create_basic_user()
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            "question": ["Incorrect type. Expected pk value, received str."]
        }
        self.assertEqual(expected_error, response_error)


class ChoicePutViewTests(ApiTestCase):
    def test_put_choice_successfully(self):
        """
        Update an existing choice without errors
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice", question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1, created_by=user
        )
        choice_new_data = {
            "choice_text": "Some other choice",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=200
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(choice_new_data)), response_data)

    def test_put_choice_exclude_required_fields(self):
        """
        Fail to update an existing choice
        because a required field is not included
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice", question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1, created_by=user
        )
        required_fields = ("choice_text", "question")
        choice_original_data = {
            "choice_text": "Some other choice",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        for required_field in required_fields:
            choice_new_data = {
                key: value
                for (key, value) in choice_original_data.items()
                if key is not required_field
            }
            token = self.login(user.username, user_password)
            response = self.put(
                target_url, token, data=choice_new_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)

    def test_put_choice_blank_choice_text(self):
        """
        Fail to update an existing choice because choice_text is blank
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice", question=question_instance
        )
        choice_new_data = {
            "choice_text": "",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"choice_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)

    def test_put_choice_null_question(self):
        """
        Fail to update an existing choice because question is null
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice", question=question_instance
        )
        choice_new_data = {"choice_text": "Some choice", "question": ""}
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question": ["This field may not be null."]}
        self.assertEqual(expected_error, response_error)

    def test_put_choice_not_question_pk(self):
        """
        Fail to update an existing choice because question is not a numeric id
        """
        user, user_password = create_basic_user(
            return_json=False, return_plain_password=True
        )
        question_instance = create_question(
            question_text="Some question.", days=30, created_by=user
        )
        choice_instance = create_choice(
            choice_text="Some choice", question=question_instance
        )
        choice_new_data = {
            "choice_text": "Some choice",
            "question": "some question",
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        token = self.login(user.username, user_password)
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            "question": ["Incorrect type. Expected pk value, received str."]
        }
        self.assertEqual(expected_error, response_error)


class UserPostViewTests(ApiTestCase):
    def test_post_user_successfully(self):
        """
        Create a new user without errors
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        allowed_fields = get_allowed_fields_of_entity("User")
        expected_data = entity_to_dict(
            user_instance,
            allowed_fields,
            fields={
                "id",
                "password",
                "is_superuser",
                "username",
                "first_name",
                "last_name",
                "email",
                "is_staff",
                "is_active",
                "groups",
                "user_permissions",
            },
        )
        expected_data["groups"] = list(expected_data["groups"].all())
        expected_data["user_permissions"] = list(
            expected_data["user_permissions"].all()
        )
        User.objects.all().delete()
        target_url = "/api/polls/user/"
        user, user_password = create_basic_user()
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=user_data, expected_response_status=201
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(expected_data.pop("id"), int)
        self.assertLess(len(user_data["password"]), len(expected_data.pop("password")))
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertLess(len(user_data["password"]), len(response_data.pop("password")))
        self.assertEqual(expected_data, response_data)

    def test_post_user_exclude_required_fields(self):
        """
        Fail to create a new user because some or all required field were not included
        """
        base_user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        required_fields = {"username", "password"}
        target_url = "/api/polls/user/"
        for required_field in required_fields:
            user_data = {
                key: value
                for (key, value) in base_user_data.items()
                if key != required_field
            }
            user, user_password = create_basic_user()
            token = self.login(user.username, user_password)
            response = self.post(
                target_url, token, data=user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)

        user_data = {
            key: value
            for (key, value) in base_user_data.items()
            if key not in required_fields
        }
        user, user_password = create_basic_user()
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=user_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {key: ["This field is required."] for key in required_fields}
        self.assertEqual(expected_error, response_error)

    def test_post_user_blank_fields(self):
        """
        Fail to create a new user because some required field is blank
        """
        base_user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        required_fields = {"username", "password"}
        target_url = "/api/polls/user/"
        for required_field in required_fields:
            user_data = deepcopy(base_user_data)
            user_data[required_field] = ""
            user, user_password = create_basic_user()
            token = self.login(user.username, user_password)
            response = self.post(
                target_url, token, data=user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field may not be blank."]}
            self.assertEqual(expected_error, response_error)

        user_data = {
            key: "" for (key, value) in base_user_data.items() if key in required_fields
        }
        user, user_password = create_basic_user()
        token = self.login(user.username, user_password)
        response = self.post(
            target_url, token, data=user_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            key: ["This field may not be blank."] for key in required_fields
        }
        self.assertEqual(expected_error, response_error)

    def test_post_user_invalid_email(self):
        """
        Fail to create a new user because an invalid email is provided
        """
        user_data = {
            "username": "test",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        invalid_emails = {1, "1", "1@", "1@gmail", "test@.com"}
        target_url = "/api/polls/user/"
        for invalid_email in invalid_emails:
            user_data["email"] = invalid_email
            user, user_password = create_basic_user()
            token = self.login(user.username, user_password)
            response = self.post(
                target_url, token, data=user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {"email": ["Enter a valid email address."]}
            self.assertEqual(expected_error, response_error)


class UserPutViewTests(ApiTestCase):
    def test_put_user_successfully(self):
        """
        Update an existing user without errors
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        allowed_fields = get_allowed_fields_of_entity("User")
        expected_data = entity_to_dict(
            user_instance,
            allowed_fields,
            fields={
                "id",
                "password",
                "is_superuser",
                "username",
                "first_name",
                "last_name",
                "email",
                "is_staff",
                "is_active",
                "groups",
                "user_permissions",
            },
        )
        expected_data["groups"] = list(expected_data["groups"].all())
        expected_data["user_permissions"] = list(
            expected_data["user_permissions"].all()
        )
        new_user_data = {
            "username": "test_1",
            "email": "test_1@gmail.com",
            "password": "12345",
            "first_name": "Mr. Test 1",
            "last_name": "Unit 2",
        }
        expected_data.update(new_user_data)
        target_url = "/api/polls/user/%s/" % expected_data["id"]
        token = self.login(user_instance.username, user_data["password"])
        response = self.put(
            target_url, token, data=new_user_data, expected_response_status=200
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(expected_data.pop("id"), int)
        self.assertLess(len(user_data["password"]), len(expected_data.pop("password")))
        self.assertLess(len(user_data["password"]), len(response_data.pop("password")))
        self.assertEqual(expected_data, response_data)

    def test_put_user_exclude_required_fields(self):
        """
        Fail to update an existing user because some or all required field were not included
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        base_new_user_data = {
            "username": "test_1",
            "email": "test_1@gmail.com",
            "password": "12345",
            "first_name": "Mr. Test 1",
            "last_name": "Unit 2",
        }
        target_url = "/api/polls/user/%s/" % user_instance.id
        required_fields = {"username", "password"}

        for required_field in required_fields:
            new_user_data = {
                key: value
                for (key, value) in base_new_user_data.items()
                if key != required_field
            }
            token = self.login(user_instance.username, user_data["password"])
            response = self.put(
                target_url, token, data=new_user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field is required."]}
            self.assertEqual(expected_error, response_error)

        new_user_data = {
            key: value
            for (key, value) in base_new_user_data.items()
            if key not in required_fields
        }
        token = self.login(user_instance.username, user_data["password"])
        response = self.put(
            target_url, token, data=new_user_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {key: ["This field is required."] for key in required_fields}
        self.assertEqual(expected_error, response_error)

    def test_put_user_blank_fields(self):
        """
        Fail to update an existing user because some required field is blank
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        base_new_user_data = {
            "username": "test_1",
            "email": "test_1@gmail.com",
            "password": "12345",
            "first_name": "Mr. Test 1",
            "last_name": "Unit 2",
        }
        target_url = "/api/polls/user/%s/" % user_instance.id
        required_fields = {"username", "password"}

        for required_field in required_fields:
            new_user_data = deepcopy(base_new_user_data)
            new_user_data[required_field] = ""
            token = self.login(user_instance.username, user_data["password"])
            response = self.put(
                target_url, token, data=new_user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field may not be blank."]}
            self.assertEqual(expected_error, response_error)

        new_user_data = deepcopy(base_new_user_data)
        new_user_data = {
            key: "" for (key, value) in new_user_data.items() if key in required_fields
        }
        token = self.login(user_instance, user_data["password"])
        response = self.put(
            target_url, token, data=new_user_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            key: ["This field may not be blank."] for key in required_fields
        }
        self.assertEqual(expected_error, response_error)

    def test_put_user_invalid_email(self):
        """
        Fail to update an existing user because an invalid email is provided
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        new_user_data = {
            "username": "test_1",
            "password": "12345",
            "first_name": "Mr. Test 1",
            "last_name": "Unit 2",
        }
        invalid_emails = {1, "1", "1@", "1@gmail", "test@.com"}
        target_url = "/api/polls/user/%s/" % user_instance.id
        for invalid_email in invalid_emails:
            new_user_data["email"] = invalid_email
            token = self.login(user_instance.username, user_data["password"])
            response = self.put(
                target_url, token, data=new_user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {"email": ["Enter a valid email address."]}
            self.assertEqual(expected_error, response_error)


class UserDeleteViewTests(ApiTestCase):
    def test_delete_user_successfully(self):
        """
        Delete an existing user without errors
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        target_url = "/api/polls/user/%s/"
        target_url = target_url % user_instance.id
        token = self.login(user_instance.username, user_data["password"])
        response = self.delete(target_url, token, expected_response_status=204)
        expected_data = b""
        self.assertEqual(expected_data, response.content)

    def test_delete_user_non_existent(self):
        """
        Delete an existing user unsuccessfully since
        it does not exist any Question with the requested id
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        target_url = "/api/polls/user/%s/"
        non_existent_id = user_instance.id + 1
        target_url = target_url % non_existent_id
        token = self.login(user_instance.username, user_data["password"])
        response = self.delete(target_url, token, expected_response_status=404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class LoginViewTests(TestCase):
    def tests_login_successful(self):
        """
        Creates a new token without error and audits its creation
        """
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)
        login_data = {
            "username": user_instance.username,
            "password": user_data["password"],
        }
        target_url = "/api/polls/login/"
        response = self.client.post(target_url, data=login_data)
        self.assertEqual(response.status_code, 200)
        response_data = response.data
        self.assertIsInstance(response_data["token"], str)
        self.assertEqual(user_instance.id, response_data["user_id"])

    def test_login_bad_credentials(self):
        """
        Fails to create a new token because no valid credentials were provided
        """
        login_data = {"username": "invalid_username", "password": "invalid_password"}
        target_url = "/api/polls/login/"
        response = self.client.post(target_url, data=login_data)
        self.assertEqual(response.status_code, 400)
        response_error = response.data
        expected_error = {
            "non_field_errors": [
                ErrorDetail(
                    string="Unable to log in with provided credentials.",
                    code="authorization",
                )
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_login_exclude_required_fields(self):
        """
        Fails to create a new token because some or
        all required fields were not provided
        """
        base_login_data = {
            "username": "invalid_username",
            "password": "invalid_password",
        }
        target_url = "/api/polls/login/"
        required_fields = set(base_login_data.keys())
        for required_field in required_fields:
            login_data = {
                key: value
                for (key, value) in base_login_data.items()
                if key != required_field
            }
            response = self.client.post(target_url, data=login_data)
            self.assertEqual(response.status_code, 400)
            response_error = response.data
            expected_error = {
                required_field: [
                    ErrorDetail(string="This field is required.", code="required")
                ]
            }
            self.assertEqual(expected_error, response_error)

        login_data = {}
        response = self.client.post(target_url, data=login_data)
        self.assertEqual(response.status_code, 400)
        response_error = response.data
        expected_error = {
            key: [ErrorDetail(string="This field is required.", code="required")]
            for key in base_login_data.keys()
        }
        self.assertEqual(expected_error, response_error)

    def test_login_blank_required_fields(self):
        """
        Fails to create a new token because some or all
        required fields were provided as empty values
        """
        base_login_data = {
            "username": "invalid_username",
            "password": "invalid_password",
        }
        target_url = "/api/polls/login/"
        required_fields = set(base_login_data.keys())
        for required_field in required_fields:
            login_data = deepcopy(base_login_data)
            login_data[required_field] = ""
            response = self.client.post(target_url, data=login_data)
            self.assertEqual(response.status_code, 400)
            response_data = response.data
            self.assertEqual(
                response_data,
                {
                    required_field: [
                        ErrorDetail(string="This field may not be blank.", code="blank")
                    ]
                },
            )

        login_data = {key: "" for (key, value) in base_login_data.items()}
        response = self.client.post(target_url, data=login_data)
        self.assertEqual(response.status_code, 400)
        response_error = response.data
        expected_error = {
            key: [ErrorDetail(string="This field may not be blank.", code="blank")]
            for key in base_login_data.keys()
        }
        self.assertEqual(expected_error, response_error)
