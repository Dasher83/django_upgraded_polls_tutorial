import datetime
import json
from copy import deepcopy

from django.test import TestCase
from django.utils import timezone

from polls.models import Question, Choice


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


def choice_to_dict(choice_instance, fields=()):
    """
    Translates an instance of a Choice into a dictionary representation
    """
    representation = {
        'id': choice_instance.id,
        'choice_text': choice_instance.choice_text,
        'votes': choice_instance.votes,
        'question': choice_instance.question.id
    }
    if fields:
        allowed_fields = ('id', 'choice_text', 'votes', 'question')
        representation = {
            field: representation[field] for field in fields
            if field in allowed_fields
        }
    return representation


def question_to_dict(question_instance, fields=()):
    """
    Translates an instance of a Question into a dictionary representation
    """
    representation = {
        'id': question_instance.id,
        'question_text': question_instance.question_text,
        'pub_date': question_instance.pub_date.isoformat()
    }
    if fields:
        allowed_fields = ('id', 'question_text', 'pub_date')
        representation = {
            field: representation[field] for field in fields
            if field in allowed_fields
        }
    return representation


class QuestionIndexViewTests(TestCase):

    def test_get_no_question(self):
        """
        Obtain all questions having none
        """
        target_url = '/api/polls/question/'
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        expected_data = []
        self.assertEqual(expected_data, json.loads(response.content))

    def test_get_all_questions_successfully(self):
        """
        Obtain all questions available
        """
        expected_data = []
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        expected_data.append(question_to_dict(question_instance))
        question_instance = create_question(
            question_text="Some other question.", days=31
        )
        expected_data.append(question_to_dict(question_instance))

        target_url = '/api/polls/question/'
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_question_successfully(self):
        """
        Obtain a single Question by its id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_model_representation = question_to_dict(question_instance)
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_model_representation['id']
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        question_response_representation = json.loads(response.content)
        self.assertEqual(
            question_model_representation,
            question_response_representation
        )

    def test_get_one_question_non_existent(self):
        """
        Obtain a single Question by its id
        However, no Question has that particular id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_model_representation = question_to_dict(question_instance)
        target_url = '/api/polls/question/%s/'
        non_existent_id = str(int(question_model_representation['id']) + 1)
        target_url = target_url % non_existent_id
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 404)
        expected_response = {'detail': 'Not found.'}
        self.assertEqual(
            expected_response,
            json.loads(response.content)
        )


class QuestionPostViewTests(TestCase):
    def test_post_question_successfully(self):
        """
        Create a new question without errors
        """
        question_data = {
            'question_text': 'What is your favorite series',
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/'
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop('id'), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_post_question_exclude_pub_date(self):
        """
        Fail to create a new question because pub_-date is not included
        """
        question_data = {
            'question_text': 'some question'
        }
        target_url = '/api/polls/question/'
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'pub_date': [
                'This field is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_question_bad_format_pub_date(self):
        """
        Fail to create a new question because
        the format of the publication date is not correct
        """
        incorrect_values = ('', 'incorrect_date_format', 1)
        for incorrect_value in incorrect_values:
            question_data = {
                'question_text': 'What is your favorite series',
                'pub_date': incorrect_value
            }
            target_url = '/api/polls/question/'
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
        question_data = {
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/'
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question_text': [
                'This field is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_question_blank_question_text(self):
        """
        Fail to create a new question because question_text is blank
        """
        question_data = {
            'question_text': '',
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/'
        response = self.client.post(target_url, data=question_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question_text': [
                'This field may not be blank.'
            ]
        }
        self.assertEqual(expected_error, response_error)


class QuestionPutViewTests(TestCase):
    def test_put_question_successfully(self):
        """
        Update a new question without errors
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_data = {
            'question_text': 'What is your favorite series',
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(question_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop('id'), int)
        self.assertEqual(json.loads(json.dumps(question_data)), response_data)

    def test_put_question_exclude_pub_date(self):
        """
        Fail to update a new question because pub_date is not included
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_data = {
            'question_text': 'some other question'
        }
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(question_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'pub_date': [
                'This field is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_question_bad_format_pub_date(self):
        """
        Fail to update a new question because
        the format of the publication date is not correct
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        incorrect_values = ('', 'incorrect_date_format', 1)
        for incorrect_value in incorrect_values:
            question_data = {
                'question_text': 'What is your favorite series',
                'pub_date': incorrect_value
            }
            target_url = '/api/polls/question/%s/'
            target_url = target_url % question_instance.id
            response = self.client.put(
                target_url,
                data=json.dumps(question_data),
                content_type='application/json'
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
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_data = {
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(question_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question_text': [
                'This field is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_question_blank_question_text(self):
        """
        Fail to update a new question because question_text is blank
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        question_data = {
            'question_text': '',
            'pub_date': '2021-04-08T09:27:35-03:00'
        }
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(question_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question_text': [
                'This field may not be blank.'
            ]
        }
        self.assertEqual(expected_error, response_error)


class QuestionDeleteViewTests(TestCase):
    def test_delete_question_successfully(self):
        """
        Delete an existing question without errors
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        target_url = '/api/polls/question/%s/'
        target_url = target_url % question_instance.id
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 204)
        expected_data = b''
        self.assertEqual(expected_data, response.content)

    def test_delete_question_non_existent(self):
        """
        Delete an existing question unsuccessfully since
        it does not exist any Question with the requested id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        target_url = '/api/polls/question/%s/'
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
        target_url = '/api/polls/choice/'
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        expected_data = []
        self.assertEqual(expected_data, json.loads(response.content))

    def test_get_all_choices_successfully(self):
        """
        Obtain all choices available
        """
        expected_data = []
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        expected_data.append(choice_to_dict(choice_instance))
        choice_instance = create_choice(
            choice_text="Some other.", votes=1, question=question_instance
        )
        expected_data.append(choice_to_dict(choice_instance))

        target_url = '/api/polls/choice/'
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_data, response_data)

    def test_get_one_choice_successfully(self):
        """
        Obtain a single Choice by its id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        expected_response = choice_to_dict(choice_instance)
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % expected_response['id']
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(expected_response, response_data)

    def test_get_one_choice_non_existent(self):
        """
        Obtain a single Choice by its id
        However, no Choice has that particular id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        choice_representation = choice_to_dict(choice_instance)
        target_url = '/api/polls/choice/%s/'
        non_existent_id = str(int(choice_representation['id']) + 1)
        target_url = target_url % non_existent_id
        response = self.client.get(target_url)
        self.assertEqual(response.status_code, 404)
        expected_response = {'detail': 'Not found.'}
        self.assertEqual(
            expected_response,
            json.loads(response.content)
        )


class ChoiceDeleteViewTests(TestCase):
    def test_delete_choice_successfully(self):
        """
        Delete an existing choice without errors
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.delete(target_url)
        self.assertEqual(response.status_code, 204)
        expected_data = b''
        self.assertEqual(expected_data, response.content)

    def test_delete_choice_non_existent(self):
        """
        Delete an existing choice unsuccessfully since
        it does not exist any choice with the requested id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice.", votes=1, question=question_instance
        )
        target_url = '/api/polls/choice/%s/'
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
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/'
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop('id'), int)
        self.assertEqual(json.loads(json.dumps(choice_data)), response_data)

    def test_post_choice_exclude_required_fields(self):
        """
        Fail to create a new choice because a required field is not included
        """
        required_fields = ('choice_text', 'question')
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        original_choice_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': question_instance.id
        }
        for required_field in required_fields:
            choice_data = {
                key: value for (key, value) in original_choice_data.items()
                if key is not required_field
            }
            target_url = '/api/polls/choice/'
            response = self.client.post(target_url, data=choice_data)
            self.assertEqual(response.status_code, 400)
            response_error = json.loads(response.content)
            expected_error = {
                required_field: [
                    'This field is required.'
                ]
            }
            self.assertEqual(expected_error, response_error)

    def test_post_choice_blank_choice_text(self):
        """
        Fail to create a new choice because choice_text is blank
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_data = {
            'choice_text': '',
            'votes': 5,
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/'
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'choice_text': [
                'This field may not be blank.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_choice_null_question(self):
        """
        Fail to create a new choice because question is null
        """
        choice_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': ''
        }
        target_url = '/api/polls/choice/'
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question': [
                'This field may not be null.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_choice_not_question_pk(self):
        """
        Fail to create a new choice because question is not a numeric id
        """
        choice_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': 'some question'
        }
        target_url = '/api/polls/choice/'
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question': [
                'Incorrect type. Expected pk value, received str.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_post_choice_non_numeric_votes(self):
        """
        Fail to create a new choice because votes is not a numeric value
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_data = {
            'choice_text': 'Some choice',
            'votes': 'some value',
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/'
        response = self.client.post(target_url, data=choice_data)
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'votes': [
                'A valid integer is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)


class ChoicePutViewTests(TestCase):
    def test_put_choice_successfully(self):
        """
        Update an existing choice without errors
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1
        )
        choice_new_data = {
            'choice_text': 'Some other choice',
            'votes': 5,
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data.pop('id'), int)
        self.assertEqual(json.loads(json.dumps(choice_new_data)), response_data)

    def test_put_choice_exclude_required_fields(self):
        """
        Fail to update an existing choice
        because a required field is not included
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        question_instance = create_question(
            question_text="Some other question.", days=1
        )
        required_fields = ('choice_text', 'question')
        choice_original_data = {
            'choice_text': 'Some other choice',
            'votes': 5,
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        for required_field in required_fields:
            choice_new_data = {
                key: value for (key, value) in choice_original_data.items()
                if key is not required_field
            }
            response = self.client.put(
                target_url,
                data=json.dumps(choice_new_data),
                content_type='application/json')
            self.assertEqual(response.status_code, 400)
            response_error = json.loads(response.content)
            expected_error = {
                required_field: [
                    'This field is required.'
                ]
            }
            self.assertEqual(expected_error, response_error)

    def test_put_choice_blank_choice_text(self):
        """
        Fail to update an existing choice because choice_text is blank
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            'choice_text': '',
            'votes': 5,
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'choice_text': [
                'This field may not be blank.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_choice_null_question(self):
        """
        Fail to update an existing choice because question is null
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': ''
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question': [
                'This field may not be null.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_choice_not_question_pk(self):
        """
        Fail to update an existing choice because question is not a numeric id
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            'choice_text': 'Some choice',
            'votes': 5,
            'question': 'some question'
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'question': [
                'Incorrect type. Expected pk value, received str.'
            ]
        }
        self.assertEqual(expected_error, response_error)

    def test_put_choice_non_numeric_votes(self):
        """
        Fail to update an existing choice because votes is not a numeric value
        """
        question_instance = create_question(
            question_text="Some question.", days=30
        )
        choice_instance = create_choice(
            choice_text="Some choice", votes=2, question=question_instance
        )
        choice_new_data = {
            'choice_text': 'Some choice',
            'votes': 'some value',
            'question': question_instance.id
        }
        target_url = '/api/polls/choice/%s/'
        target_url = target_url % choice_instance.id
        response = self.client.put(
            target_url,
            data=json.dumps(choice_new_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        response_error = json.loads(response.content)
        expected_error = {
            'votes': [
                'A valid integer is required.'
            ]
        }
        self.assertEqual(expected_error, response_error)
