from django.test import TestCase

from . import views


class TestQuizView(TestCase):
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
