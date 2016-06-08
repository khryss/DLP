from django.test import TestCase

from . import views


class QuizView(TestCase):
    def test_quiz_view_find_first_option(self):
        views._find_first_option([])
