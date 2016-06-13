from django.test import TestCase
from django.core.exceptions import ValidationError

import mock

from .. import views
from ..models import Question, Option


class TestQuizView(TestCase):
    def setUp(self):
        class DummyRequest:
            session = {}
            POST = {}
        self.DummyRequest = DummyRequest

        self.view = views.QuizView()
        self.quiz_id = 0
        self.questions_per_page = 2

        it_scores = iter([10, 0, -7, 18, 22, -40])

        o_idx = 1
        for q_idx in range(3):
            q = Question.objects.create(quiz_id=self.quiz_id,
                                        text='question_text_' + str(q_idx))
            for _ in range(2):
                Option.objects.create(question_id=q.id,
                                      scor=it_scores.next(),
                                      text='option_text_' + str(o_idx))
                o_idx += 1

        self.expected_qustion_list = [{'question_text': 'question_text_0',
                                       'options': {'option_1': 'option_text_1',
                                                   'option_2': 'option_text_2'}},
                                      {'question_text': 'question_text_1',
                                       'options': {'option_3': 'option_text_3',
                                                   'option_4': 'option_text_4'}},
                                      {'question_text': 'question_text_2',
                                       'options': {'option_5': 'option_text_5',
                                                   'option_6': 'option_text_6'}}]
        self.expected_selected_options = {'option_1': {'is_selected': False,
                                                       'score': 10},
                                          'option_2': {'is_selected': False,
                                                       'score': 0},
                                          'option_3': {'is_selected': False,
                                                       'score': -7},
                                          'option_4': {'is_selected': False,
                                                       'score': 18},
                                          'option_5': {'is_selected': False,
                                                       'score': 22},
                                          'option_6': {'is_selected': False,
                                                       'score': -40},
                                          }

    def test_question_mapping(self):
        self.maxDiff = None
        given = Question.objects.all()

        result_questions, result_options = self.view.get_question_mapping(given)
        self.assertEqual(result_questions, self.expected_qustion_list)
        self.assertEqual(result_options, self.expected_selected_options)

    def test_validate_min_options_selected(self):
        given_qustions = [{'question_text': 'question_text_0',
                           'options': {'option_1': 'option_text_1',
                                       'option_2': 'option_text_2'}},
                          {'question_text': 'question_text_1',
                           'options': {'option_3': 'option_text_3',
                                       'option_4': 'option_text_4'}}]
        given_options = {'option_1': {'is_selected': False,
                                      'score': 0},
                         'option_2': {'is_selected': False,
                                      'score': 0},
                         'option_3': {'is_selected': False,
                                      'score': 0},
                         'option_4': {'is_selected': False,
                                      'score': 0},
                         }

        # no option selected
        try:
            self.view._validate_min_options_selected(given_qustions, given_options)
            self.fail('_validate_min_options_selected method did not raise an exception.')
        except:
            pass

        # one option selected on one question
        given_options['option_4']['is_selected'] = True
        try:
            self.view._validate_min_options_selected(given_qustions, given_options)
            self.fail('_validate_min_options_selected method did not raise an exception.')
        except:
            pass

        # one option selected on both questions
        given_options['option_1']['is_selected'] = True
        try:
            self.view._validate_min_options_selected(given_qustions, given_options)
        except:
            self.fail('_validate_min_options_selected method raised an exception.')

        # all options selected
        given_options['option_2']['is_selected'] = True
        given_options['option_3']['is_selected'] = True
        try:
            self.view._validate_min_options_selected(given_qustions, given_options)
        except ValidationError:
            self.fail('_validate_min_options_selected method raised an exception.')

    def test_calculate_score(self):
        given_options_score = [{'score': 1},
                               {'score': -10},
                               {'score': 0},
                               {'score': 0},
                               {'score': 17}]
        result_score = self.view._calculate_score(given_options_score)
        self.assertEqual(result_score, 8)

    def test_get_context_question_list(self):
        given_questions = [{'question_text': 'question_text_0',
                            'options': {'option_1': 'option_text_1',
                                        'option_2': 'option_text_2'}},
                           {'question_text': 'question_text_1',
                            'options': {'option_3': 'option_text_3',
                                        'option_4': 'option_text_4'}}]
        given_request_session = {}
        given_request_session['selected_options'] = {
            'option_1': {'is_selected': False},
            'option_2': {'is_selected': False},
            'option_3': {'is_selected': False},
            'option_4': {'is_selected': False},
        }

        expected_result = [('question_text_0', [('option_2', 'option_text_2', False),
                                                ('option_1', 'option_text_1', False)]),
                           ('question_text_1', [('option_3', 'option_text_3', False),
                                                ('option_4', 'option_text_4', False)])]
        result = self.view._get_context_question_list(given_questions,
                                                      given_request_session)
        self.assertEqual(result, expected_result)

    def test_calculate_max_score(self):
        given_options = {'option_1': {'score': 0},
                         'option_2': {'score': 10},
                         'option_3': {'score': -7},
                         'option_4': {'score': -20},
                         }
        result_score = self.view._calculate_max_score(given_options)
        self.assertEqual(result_score, 10)

    def test_find_best_option(self):
        view = views.QuizView()

        given_options = [{'id': 'op1', 'text': '', 'is_sel': False, 'score': 10},
                         {'id': 'op2', 'text': '', 'is_sel': False, 'score': 0},
                         {'id': 'op3', 'text': '', 'is_sel': False, 'score': -1},
                         {'id': 'op4', 'text': '', 'is_sel': True, 'score': 5},
                         {'id': 'op5', 'text': '', 'is_sel': True, 'score': -3}]
        # smallest not selected
        result = view._find_best_option(given_options, selected=False, positive=False)
        self.assertEqual(result['id'], 'op3')
        self.assertEqual(result['score'], -1)

        # smallest selected
        result = view._find_best_option(given_options, selected=True, positive=False)
        self.assertEqual(result['id'], 'op5')
        self.assertEqual(result['score'], -3)

        # biggest not selected
        result = view._find_best_option(given_options, selected=False, positive=True)
        self.assertEqual(result['id'], 'op1')
        self.assertEqual(result['score'], 10)

        # biggest selected
        result = view._find_best_option(given_options, selected=True, positive=True)
        self.assertEqual(result['id'], 'op4')
        self.assertEqual(result['score'], 5)

        given_options = [{'id': 'op1', 'text': '', 'is_sel': True, 'score': 10},
                         {'id': 'op2', 'text': '', 'is_sel': True, 'score': 0},
                         {'id': 'op3', 'text': '', 'is_sel': True, 'score': -1},
                         {'id': 'op4', 'text': '', 'is_sel': True, 'score': 5},
                         {'id': 'op5', 'text': '', 'is_sel': True, 'score': -3}]

        # smallest not selected when all selected
        result = view._find_best_option(given_options, selected=False, positive=False)
        self.assertTrue(result is None)

    def test_compute_sugestions(self):
        given_qustions = [{'question_text': 'question_text_0',
                           'options': {'option_1': 'option_text_1',
                                       'option_2': 'option_text_2',
                                       'option_3': 'option_text_3'}},
                          {'question_text': 'question_text_1',
                           'options': {'option_4': 'option_text_4',
                                       'option_5': 'option_text_5',
                                       'option_6': 'option_text_6'}},
                          {'question_text': 'question_text_2',
                           'options': {'option_7': 'option_text_7',
                                       'option_8': 'option_text_8',
                                       'option_9': 'option_text_9'}}]

        given_request_session = {}
        given_request_session['selected_options'] = {
            # question 0
            'option_1': {'is_selected': False,
                         'score': 10},
            'option_2': {'is_selected': True,
                         'score': 0},
            'option_3': {'is_selected': False,
                         'score': -10},
            # question 1
            'option_4': {'is_selected': True,
                         'score': -1},
            'option_5': {'is_selected': False,
                         'score': 2},
            'option_6': {'is_selected': False,
                         'score': -1},
            # question 2
            'option_7': {'is_selected': True,
                         'score': -1},
            'option_8': {'is_selected': True,
                         'score': 2},
            'option_9': {'is_selected': False,
                         'score': -1},
        }

        expected_result = [(('for best: question_text_0<option_text_2> -> <option_text_1>', 10),
                            ('for worst: question_text_0<option_text_2> -> <option_text_3>', -10)),
                           (('for best: No sugestion to improve score', 0),
                            ('for worst: question_text_2<option_text_8> -> <option_text_9>', -3))]
        result = self.view._compute_sugestions(given_qustions,
                                               given_request_session,
                                               self.questions_per_page)

        self.assertEqual(result, expected_result)

    def test_init_session(self):
        temp_request = self.DummyRequest()
        temp_request.session = {'fake_attribute_for_clear': 0}

        self.view._init_session(temp_request, self.quiz_id)

        try:
            temp_request.session['fake_attribute_for_clear']
            self.fail('The session not cleared before init.')
        except KeyError:
            pass
        self.assertEqual(temp_request.session['quiz_id'], self.quiz_id)
        self.assertEqual(temp_request.session['current_page_no'], 0)
        self.assertEqual(temp_request.session['question_list'], self.expected_qustion_list)
        self.assertEqual(temp_request.session['selected_options'], self.expected_selected_options)
        self.assertEqual(temp_request.session['last_page_no'],
                         (len(self.expected_qustion_list) / self.questions_per_page))

    @mock.patch('quiz.views.QuizView._calculate_score')
    @mock.patch('quiz.views.QuizView._validate_min_options_selected')
    def test_handle_post_request(self, mock_validate, mock_calculate_score):
        temp_request = self.DummyRequest()

        # 'Previous'
        temp_request.session['selected_options'] = self.expected_selected_options
        temp_request.session['current_page_no'] = 1
        temp_request.session['last_page_no'] = \
            len(self.expected_qustion_list) / self.questions_per_page
        temp_request.session['current_score'] = [0] * (
            temp_request.session['last_page_no'] + 1)
        temp_request.POST = {'Previous': None}

        given_page_qustions = self.expected_qustion_list[:2]
        self.view._handle_post_request(temp_request,
                                       given_page_qustions,
                                       self.quiz_id)

        current_page = 0
        self.assertEqual(temp_request.session['current_page_no'], current_page)

        # 'Next'/'Finish' without error
        mock_calculate_score.side_effect = [mock.sentinel.calculated_score]
        temp_request.POST = {'Next': None}

        self.view._handle_post_request(temp_request,
                                       given_page_qustions,
                                       self.quiz_id)

        current_page += 1
        self.assertEqual(temp_request.session['current_score'][current_page - 1],
                         mock.sentinel.calculated_score)
        self.assertEqual(temp_request.session['current_page_no'],
                         current_page)
        with self.assertRaises(KeyError):
            temp_request.session['error']

        # 'Next'/'Finish' with error
        def mock_raise_validation(page_question_list, selected_options):
            raise ValidationError('Error message.')
        mock_validate.side_effect = mock_raise_validation

        self.view._handle_post_request(temp_request,
                                       given_page_qustions,
                                       self.quiz_id)

        self.assertTrue(temp_request.session['error'])
        self.assertEqual(temp_request.session['current_page_no'],
                         current_page)
        self.assertEqual(temp_request.session['current_score'][current_page - 1],
                         mock.sentinel.calculated_score)

    @mock.patch('quiz.views.render')
    @mock.patch('quiz.views.QuizView._compute_sugestions')
    @mock.patch('quiz.views.QuizView._calculate_max_score')
    def test_handle_get_request(self,
                                mock_calculate_max_score,
                                mock_compute_sugestions,
                                mock_render):
        temp_request = self.DummyRequest()

        mock_calculate_max_score.side_effect = [mock.sentinel.max_score]
        mock_compute_sugestions.side_effect = [mock.sentinel.sugestions]

        # result page without error
        current_page = 2
        temp_request.session['selected_options'] = self.expected_selected_options
        temp_request.session['current_page_no'] = current_page
        temp_request.session['current_score'] = [1, 3]
        temp_request.session['last_page_no'] = \
            len(self.expected_qustion_list) / self.questions_per_page

        self.view._handle_get_request(temp_request,
                                      self.expected_qustion_list,
                                      self.expected_qustion_list[:2],
                                      self.quiz_id)

        self.assertEqual(temp_request.session, {})
        expected_context = {'score': 4,
                            'max_score': mock.sentinel.max_score,
                            'sugestions': mock.sentinel.sugestions}
        mock_render.assert_called_with(temp_request,
                                       self.view.result_template_name,
                                       expected_context)

        # result page with error
        current_page = 2
        temp_request.session['error'] = True
        temp_request.session['selected_options'] = self.expected_selected_options
        temp_request.session['current_page_no'] = current_page
        temp_request.session['current_score'] = [1, 3]
        temp_request.session['last_page_no'] = \
            len(self.expected_qustion_list) / self.questions_per_page

        self.view._handle_get_request(temp_request,
                                      self.expected_qustion_list,
                                      self.expected_qustion_list[:2],
                                      self.quiz_id)

        expected_context = {
            'quiz_id': 0,
            'current_page': 1,
            'error': True,
            'questions': [('question_text_0', [('option_2', 'option_text_2', False),
                                               ('option_1', 'option_text_1', False)]),
                          ('question_text_1', [('option_3', 'option_text_3', False),
                                               ('option_4', 'option_text_4', False)])],
            'is_last_page': True
        }
        mock_render.assert_called_with(temp_request,
                                       self.view.template_name,
                                       expected_context)

    @mock.patch('quiz.views.QuizView._handle_post_request')
    @mock.patch('quiz.views.QuizView._handle_get_request')
    @mock.patch('quiz.views.QuizView._init_session')
    def test__call__(self,
                     mock_init_session,
                     mock_handle_get_request,
                     mock_handle_post_request):

        def _mock_init_session(request, quiz_id):
            request.session['question_list'] = self.expected_qustion_list
            request.session['current_page_no'] = 0

        temp_request = self.DummyRequest()

        # get with uninitialised request.session
        temp_request.method = 'GET'
        mock_init_session.side_effect = _mock_init_session

        self.view.__call__(temp_request, self.quiz_id)

        mock_handle_get_request.assert_called_with(temp_request,
                                                   self.expected_qustion_list,
                                                   self.expected_qustion_list[:
                                                        self.questions_per_page],
                                                   self.quiz_id)

        # post
        temp_request.method = 'POST'

        self.view.__call__(temp_request, self.quiz_id)

        mock_handle_post_request.assert_called_with(temp_request,
                                                    self.expected_qustion_list[:
                                                        self.questions_per_page],
                                                    self.quiz_id)
