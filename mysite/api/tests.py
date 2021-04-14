import datetime
import json
from copy import deepcopy
from random import randint

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ErrorDetail

from polls.models import Question, Choice, User


class ApiTestCase(TestCase):
    @staticmethod
    def create_basic_user():
        user_data = {
            "username": "basic_user",
            "password": "1234",
            "email": "",
            "first_name": "",
            "last_name": "",
        }
        User.objects.filter(username=user_data["username"]).delete()
        User.create_user(**user_data)
        return user_data

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


def create_question(question_text, days):
    """
    Create a question with the given 'question_text' and published the given
    number of 'days' offset to now (negative for questions published in the
    past, positive for questions that have yet to be published).
    """
    time = timezone.localtime(timezone.now()) + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choice(choice_text, votes, question):
    """
    Create a choice with the given 'choice_text' and with a certain
    amount of 'votes' related to the given 'question'
    """
    return Choice.objects.create(
        choice_text=choice_text, votes=votes, question=question
    )


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
        "Choice": {"id", "choice_text", "votes", "question"},
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
        question_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
        }
        target_url = "/api/polls/question/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=question_data, expected_response_status=201
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_post_question_exclude_pub_date(self):
        """
        Fail to create a new question because pub_-date is not included
        """
        question_data = {"question_text": "some question"}
        target_url = "/api/polls/question/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"pub_date": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_post_question_bad_format_pub_date(self):
        """
        Fail to create a new question because
        the format of the publication date is not correct
        """
        incorrect_values = ("", "incorrect_date_format", 1)
        for incorrect_value in incorrect_values:
            question_data = {
                "question_text": "What is your favorite series",
                "pub_date": incorrect_value,
            }
            target_url = "/api/polls/question/"
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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

    def test_post_question_exclude_question_text(self):
        """
        Fail to create a new question because question_text is not included
        """
        question_data = {"pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_post_question_blank_question_text(self):
        """
        Fail to create a new question because question_text is blank
        """
        question_data = {"question_text": "", "pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=question_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)


class QuestionPutViewTests(ApiTestCase):
    def test_put_question_successfully(self):
        """
        Update a new question without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_new_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=question_new_data, expected_response_status=200
        )
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_new_data)), response_data)

    def test_put_question_exclude_pub_date(self):
        """
        Fail to update a new question because pub_date is not included
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_new_data = {"question_text": "some other question"}
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=question_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"pub_date": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_put_question_bad_format_pub_date(self):
        """
        Fail to update a new question because
        the format of the publication date is not correct
        """
        question_instance = create_question(question_text="Some question.", days=30)
        incorrect_values = ("", "incorrect_date_format", 1)
        for incorrect_value in incorrect_values:
            question_new_data = {
                "question_text": "What is your favorite series",
                "pub_date": incorrect_value,
            }
            target_url = "/api/polls/question/%s/"
            target_url = target_url % question_instance.id
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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

    def test_put_question_exclude_question_text(self):
        """
        Fail to update a new question because question_text is not included
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_new_data = {"pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=question_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_put_question_blank_question_text(self):
        """
        Fail to update a new question because question_text is blank
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_new_data = {
            "question_text": "",
            "pub_date": "2021-04-08T09:27:35-03:00",
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=question_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)


class QuestionDeleteViewTests(ApiTestCase):
    def test_delete_question_successfully(self):
        """
        Delete an existing question without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.delete(target_url, token, expected_response_status=204)
        expected_data = b""
        self.assertEqual(expected_data, response.content)

    def test_delete_question_non_existent(self):
        """
        Delete an existing question unsuccessfully since
        it does not exist any Question with the requested id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        target_url = "/api/polls/question/%s/"
        non_existent_id = question_instance.id + 1
        target_url = target_url % non_existent_id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.delete(target_url, token, expected_response_status=404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class ChoiceDeleteViewTests(ApiTestCase):
    def test_delete_choice_successfully(self):
        """
        Delete an existing choice without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.delete(target_url, token, expected_response_status=204)
        expected_data = b""
        self.assertEqual(expected_data, response.content)

    def test_delete_choice_non_existent(self):
        """
        Delete an existing choice unsuccessfully since
        it does not exist any choice with the requested id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        target_url = "/api/polls/choice/%s/"
        non_existent_id = choice_instance.id + 1
        target_url = target_url % non_existent_id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.delete(target_url, token, expected_response_status=404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class ChoicePostViewTests(ApiTestCase):
    def test_post_choice_successfully(self):
        """
        Create a new choice without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_data = {
            "choice_text": "Some choice",
            "votes": 5,
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        original_choice_data = {
            "choice_text": "Some choice",
            "votes": 5,
            "question": question_instance.id,
        }
        for required_field in required_fields:
            choice_data = {
                key: value
                for (key, value) in original_choice_data.items()
                if key is not required_field
            }
            target_url = "/api/polls/choice/"
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        choice_data = {"choice_text": "", "votes": 5, "question": question_instance.id}
        target_url = "/api/polls/choice/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
        choice_data = {"choice_text": "Some choice", "votes": 5, "question": ""}
        target_url = "/api/polls/choice/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
            "votes": 5,
            "question": "some question",
        }
        target_url = "/api/polls/choice/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            "question": ["Incorrect type. Expected pk value, received str."]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_choice_non_numeric_votes(self):
        """
        Fail to create a new choice because votes is not a numeric value
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_data = {
            "choice_text": "Some choice",
            "votes": "some value",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/"
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.post(
            target_url, token, data=choice_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"votes": ["A valid integer is required."]}
        self.assertEqual(expected_error, response_error)


class ChoicePutViewTests(ApiTestCase):
    def test_put_choice_successfully(self):
        """
        Update an existing choice without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1
        )
        choice_new_data = {
            "choice_text": "Some other choice",
            "votes": 5,
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1
        )
        required_fields = ("choice_text", "question")
        choice_original_data = {
            "choice_text": "Some other choice",
            "votes": 5,
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
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            "choice_text": "",
            "votes": 5,
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {"choice_text": "Some choice", "votes": 5, "question": ""}
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            "choice_text": "Some choice",
            "votes": 5,
            "question": "some question",
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {
            "question": ["Incorrect type. Expected pk value, received str."]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_choice_non_numeric_votes(self):
        """
        Fail to update an existing choice because votes is not a numeric value
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            "choice_text": "Some choice",
            "votes": "some value",
            "question": question_instance.id,
        }
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % choice_instance.id
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
        response = self.put(
            target_url, token, data=choice_new_data, expected_response_status=400
        )
        response_error = json.loads(response.content)
        expected_error = {"votes": ["A valid integer is required."]}
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
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
            response = self.post(
                target_url, token, data=user_data, expected_response_status=400
            )
            response_error = json.loads(response.content)
            expected_error = {required_field: ["This field may not be blank."]}
            self.assertEqual(expected_error, response_error)

        user_data = {
            key: "" for (key, value) in base_user_data.items() if key in required_fields
        }
        user = self.create_basic_user()
        token = self.login(user["username"], user["password"])
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
            user = self.create_basic_user()
            token = self.login(user["username"], user["password"])
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
