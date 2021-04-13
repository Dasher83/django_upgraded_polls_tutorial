import datetime
import json
from copy import deepcopy
from random import randint

from django.test import TestCase
from django.utils import timezone

from polls.models import Question, Choice, User


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
        },
    }
    return entities_allowed_fields_map[entity_name]


class QuestionIndexViewTests(TestCase):
    def test_get_no_question(self):
        """
        Obtain all questions having none
        """
        target_url = "/api/polls/question/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        expected_data = []
        self.assertEqual(expected_data, json.loads(response.content))

    def test_get_all_questions_successfully(self):
        """
        Obtain all questions available
        """
        expected_data = []
        allowed_fields = get_allowed_fields_of_entity("Question")
        question_instance = create_question(question_text="Some question.", days=30)
        expected_data.append(entity_to_dict(question_instance, allowed_fields))
        question_instance = create_question(
            question_text="Some other question.", days=31
        )
        expected_data.append(entity_to_dict(question_instance, allowed_fields))
        for expected_data_item in expected_data:
            expected_data_item["pub_date"] = expected_data_item["pub_date"].isoformat()

        target_url = "/api/polls/question/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_question_successfully(self):
        """
        Obtain a single Question by its id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        allowed_fields = get_allowed_fields_of_entity("Question")
        expected_data = entity_to_dict(question_instance, allowed_fields)
        expected_data["pub_date"] = expected_data["pub_date"].isoformat()
        target_url = "/api/polls/question/%s/"
        target_url = target_url % expected_data["id"]
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_question_non_existent(self):
        """
        Obtain a single Question by its id
        However, no Question has that particular id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        allowed_fields = get_allowed_fields_of_entity("Question")
        question_model_representation = entity_to_dict(
            question_instance, allowed_fields, fields={"id"}
        )
        non_existent_id = str(int(question_model_representation["id"]) + 1)
        target_url = "/api/polls/question/%s/"
        target_url = target_url % non_existent_id
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 404)
        expected_response = {"detail": "Not found."}
        self.assertEqual(expected_response, json.loads(response.content))


class QuestionPostViewTests(TestCase):
    def test_post_question_successfully(self):
        """
        Create a new question without errors
        """
        question_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
        }
        target_url = "/api/polls/question/"
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_post_question_exclude_pub_date(self):
        """
        Fail to create a new question because pub_-date is not included
        """
        question_data = {"question_text": "some question"}
        target_url = "/api/polls/question/"
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
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
            response = self.client.post(target_url, data=question_data)
            self.assertEqual(response.status_code, 400)
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
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_post_question_blank_question_text(self):
        """
        Fail to create a new question because question_text is blank
        """
        question_data = {"question_text": "", "pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/"
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)


class QuestionPutViewTests(TestCase):
    def test_put_question_successfully(self):
        """
        Update a new question without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_data = {
            "question_text": "What is your favorite series",
            "pub_date": "2021-04-08T09:27:35-03:00",
        }
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url, data=json.dumps(question_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop("id"), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_put_question_exclude_pub_date(self):
        """
        Fail to update a new question because pub_date is not included
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_data = {"question_text": "some other question"}
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url, data=json.dumps(question_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
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
            question_data = {
                "question_text": "What is your favorite series",
                "pub_date": incorrect_value,
            }
            target_url = "/api/polls/question/%s/"
            target_url = target_url % question_instance.id
            response = self.client.put(
                target_url,
                data=json.dumps(question_data),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)
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
        question_data = {"pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url, data=json.dumps(question_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field is required."]}
        self.assertEqual(expected_error, response_error)

    def test_put_question_blank_question_text(self):
        """
        Fail to update a new question because question_text is blank
        """
        question_instance = create_question(question_text="Some question.", days=30)
        question_data = {"question_text": "", "pub_date": "2021-04-08T09:27:35-03:00"}
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url, data=json.dumps(question_data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"question_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)


class QuestionDeleteViewTests(TestCase):
    def test_delete_question_successfully(self):
        """
        Delete an existing question without errors
        """
        question_instance = create_question(question_text="Some question.", days=30)
        target_url = "/api/polls/question/%s/"
        target_url = target_url % question_instance.id
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 204)
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
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class ChoiceIndexViewTests(TestCase):
    def test_get_no_choices(self):
        """
        Obtain all choices having none
        """
        target_url = "/api/polls/choice/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        expected_data = []
        self.assertEqual(expected_data, json.loads(response.content))

    def test_get_all_choices_successfully(self):
        """
        Obtain all choices available
        """
        expected_data = []
        allowed_fields = get_allowed_fields_of_entity("Choice")
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        expected_data.append(entity_to_dict(choice_instance, allowed_fields))
        choice_instance = create_choice(
            choice_text="Some other.", votes=1, question=question_instance
        )
        expected_data.append(entity_to_dict(choice_instance, allowed_fields))
        for data in expected_data:
            data["question"] = data["question"].id

        target_url = "/api/polls/choice/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_choice_successfully(self):
        """
        Obtain a single Choice by its id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        allowed_fields = get_allowed_fields_of_entity("Choice")
        expected_response = entity_to_dict(choice_instance, allowed_fields)
        expected_response["question"] = expected_response["question"].id
        target_url = "/api/polls/choice/%s/"
        target_url = target_url % expected_response["id"]
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_response, response_data)

    def test_get_one_choice_non_existent(self):
        """
        Obtain a single Choice by its id
        However, no Choice has that particular id
        """
        question_instance = create_question(question_text="Some question.", days=30)
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        allowed_fields = get_allowed_fields_of_entity("Choice")
        choice_representation = entity_to_dict(
            choice_instance, allowed_fields, fields={"id"}
        )
        target_url = "/api/polls/choice/%s/"
        non_existent_id = str(int(choice_representation["id"]) + 1)
        target_url = target_url % non_existent_id
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 404)
        expected_response = {"detail": "Not found."}
        self.assertEqual(expected_response, json.loads(response.content))


class ChoiceDeleteViewTests(TestCase):
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
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 204)
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
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 404)
        response_error = json.loads(json.dumps(str(response.content)))
        expected_error = 'b\'{"detail":"Not found."}\''
        self.assertEqual(expected_error, response_error)


class ChoicePostViewTests(TestCase):
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
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 201)
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
            response = self.client.post(target_url, data=choice_data)
            self.assertEqual(response.status_code, 400)
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
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"choice_text": ["This field may not be blank."]}
        self.assertEqual(expected_error, response_error)

    def test_post_choice_null_question(self):
        """
        Fail to create a new choice because question is null
        """
        choice_data = {"choice_text": "Some choice", "votes": 5, "question": ""}
        target_url = "/api/polls/choice/"
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
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
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
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
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"votes": ["A valid integer is required."]}
        self.assertEqual(expected_error, response_error)


class ChoicePutViewTests(TestCase):
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
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
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
            response = self.client.put(
                target_url,
                data=json.dumps(choice_new_data),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)
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
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
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
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
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
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
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
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {"votes": ["A valid integer is required."]}
        self.assertEqual(expected_error, response_error)


class UserIndexViewTests(TestCase):
    def test_get_no_user(self):
        """
        Obtain all users having none
        """
        target_url = "/api/polls/user/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        expected_data = []
        self.assertEqual(expected_data, json.loads(response.content))

    def test_get_all_user_successfully(self):
        """
        Obtain all users available
        """
        allowed_fields = get_allowed_fields_of_entity("User")
        expected_data = []
        base_user_data = {
            "username": "test_%s",
            "email": "test_%s@gmail.com",
            "password": "1234%s",
            "first_name": "Mr. Test %s",
            "last_name": "Unit %s",
        }
        fields = ("id", "username", "first_name", "last_name", "email")
        random_users_amount = randint(1, 100)
        for index in range(random_users_amount):
            user_data = {key: value % index for (key, value) in base_user_data.items()}
            user_instance = User.create_user(**user_data)
            user_representation = entity_to_dict(
                user_instance, allowed_fields, fields=fields
            )
            expected_data.append(user_representation)

        target_url = "/api/polls/user/"
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_user_successfully(self):
        """
        Obtain a single user by its id
        """
        allowed_fields = get_allowed_fields_of_entity("User")
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        fields = (
            "id",
            "is_superuser",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
        )
        user_instance = User.create_user(**user_data)
        expected_data = entity_to_dict(user_instance, allowed_fields, fields=fields)
        target_url = "/api/polls/user/%s/"
        target_url = target_url % expected_data["id"]
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_user_non_existent(self):
        """
        Obtain a single User by its id
        However, no USer has that particular id
        """
        allowed_fields = get_allowed_fields_of_entity("User")
        user_data = {
            "username": "test",
            "email": "test@gmail.com",
            "password": "1234",
            "first_name": "Mr. Test",
            "last_name": "Unit",
        }
        user_instance = User.create_user(**user_data)

        allowed_fields = get_allowed_fields_of_entity("User")
        user_representation = entity_to_dict(
            user_instance, allowed_fields, fields={"id"}
        )
        target_url = "/api/polls/user/%s/"
        non_existent_id = str(int(user_representation["id"]) + 1)
        target_url = target_url % non_existent_id
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 404)
        expected_response = {"detail": "Not found."}
        self.assertEqual(expected_response, json.loads(response.content))
