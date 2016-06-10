from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from .models import Quiz, Question

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def index_view(request):
    template_name = 'index.html'

    return render(request, template_name, {'quizs_list': Quiz.objects.all})


class QuizView(object):
    template_name = 'quiz_form.html'
    result_template_name = 'quiz_result.html'
    questions_per_page = 2

    def get_question_mapping(self, question_list):
        '''
        Maps the questions from DB into 2 structures:
          question_mapping - keeps the questions and options text
          selected_option - keeps the option select info for the session

        questions_mapping = [{'question_text': 'text',
                              'options': {'option_1': 'text',
                                          'option_2': 'text'}},
                             {'question_text': 'text',
                              'options': {'option_3': 'text'}}]
        selected_options = {'option_1': {'is_selected': False,
                                         'score': 1},
                            'option_2': {'is_selected': True,
                                         'score': 1},}}
        '''
        selected_options = {}
        questions_mapping = []

        for question in question_list:
            raw_options = question.option_set.all()

            mapped_options = {}
            for option in raw_options:
                mapped_options['option_' + str(option.id)] = option.text

                selected_options['option_' + str(option.id)] = {'is_selected': False,
                                                                'score': option.scor}

            questions_mapping.append({'question_text': question.text,
                                      'options': mapped_options})

        return questions_mapping, selected_options

    def _validate_min_options_selected(self, question_list, selected_options):
        for question in question_list:
            for option_id, _ in question['options'].items():
                if selected_options[option_id]['is_selected']:
                    break
            else:
                raise ValidationError('Please fill all questions '
                                      'with at least one option!')

    def _calculate_score(self, selected_option_list):
        page_score = 0
        for option in selected_option_list:
            page_score += option['score']
        return page_score

    def _get_context_question_list(self, page_question_list, request_session):
        '''Packs the questions info into a context list'''
        # context_question_list = [('question1', [('opt_id', 'opt_text', False),
        #                                         ('opt_id', 'opt_text', False)]),
        #                          ('question2', [('opt_id', 'opt_text', False)])]
        context_question_list = []
        for question in page_question_list:
            # options = [('opt_id', 'opt_text', False),
            #            ('opt_id', 'opt_text', True)]
            options = []
            for option_id, option_text in question['options'].items():
                is_selected = request_session['selected_options'][option_id]['is_selected']
                options.append((option_id, option_text, is_selected))

            context_question_list.append((question['question_text'], options))
        return context_question_list

    def _calculate_max_score(self, option_list):
        max_score = 0
        for _, option_info in option_list.items():
            if option_info['score'] > 0:
                max_score += option_info['score']
        return max_score

    def _find_first_option(self, options, selected=False, reverse=False): 
        # This is not a "find_first_option", it'a a "find option that improves/diminishes the score the most"
        # In this case something like _find_best_option and renaming reverse to something like positive/improve
        # and use it the same way
        filtered_options = filter(lambda x: x['is_sel'] == selected,
                                  options)
        sorted_options = sorted(filtered_options,
                                key=lambda x: x['score'],
                                reverse=reverse)
        try:
            result = filtered_options[0]
        except IndexError:
            return None

        if reverse:
            if not result['score'] > 0:
                return None
        else:
            if not result['score'] < 0:
                return None
        return result

    def _compute_sugestions(self, question_list, request_session, questions_per_page):
        question_it = iter(question_list)
        # sugestions = [[('q3<d> -> <b>', None)],
        #               [('q1<a> -> <b>', 'q2<c> -> <a>')]]
        #                (best score,    worse score)
        sugestions = []
        while True:
            try:
                page_sugestion = [None] * self.questions_per_page
                for idx in range(questions_per_page):
                    question = question_it.next()

                    options = [
                        {'id': op_id,
                         'text': op_text,
                         'is_sel': request_session['selected_options'][op_id]['is_selected'],
                         'score': request_session['selected_options'][op_id]['score']}
                        for op_id, op_text in question['options'].items()]
                    options.sort(key=lambda x: x['score']) 

                    self._find_first_option(options)
            except StopIteration:
                break
        return sugestions

    def _init_session(self, request, quiz_id):
        raw_question_list = Question.objects.filter(quiz=quiz_id).prefetch_related('option_set')

        request.session.clear()
        request.session['quiz_id'] = quiz_id
        request.session['current_page_no'] = 0

        # 'selected_options' keeps track of selected options for each session
        request.session['question_list'], request.session['selected_options'] = \
            self.get_question_mapping(raw_question_list)

        request.session['last_page_no'] = \
            len(request.session['question_list']) / self.questions_per_page

        last_page_no = request.session['last_page_no']
        request.session['current_score'] = [0] * (last_page_no + 1)

    def _handle_post_request(self, request, page_question_list, quiz_id):
        page_selected_options = []
        # update the session data with selected options from POST
        for question in page_question_list:
            for option_id, _ in question['options'].items():
                is_selected = (option_id in request.POST)
                request.session['selected_options'][option_id]['is_selected'] = is_selected
                if is_selected:
                    page_selected_options.append(request.session['selected_options'][option_id])
        if 'Previous' in request.POST:
            request.session['current_page_no'] -= 1
        elif 'Next' in request.POST or \
             'Finish' in request.POST:
            try:
                self._validate_min_options_selected(page_question_list,
                                                    request.session['selected_options'])

                current_page_no = request.session['current_page_no']
                current_score = self._calculate_score(page_selected_options)
                request.session['current_score'][current_page_no] = current_score
            except ValidationError as exception:
                request.session['error'] = exception.message
            else:
                request.session['current_page_no'] += 1

        return redirect('quiz', quiz_id=quiz_id)

    def _handle_get_request(self, request, question_list, page_question_list, quiz_id):
        error = request.session.get('error', None)
        request.session['error'] = None
        if request.session['current_page_no'] > request.session['last_page_no']:
            if not error:
                # create the result page
                score = sum(request.session['current_score'])
                max_score = self._calculate_max_score(request.session['selected_options'])
                sugestions = self._compute_sugestions(question_list,
                                                      request.session,
                                                      self.questions_per_page)
                context = {'score': score,
                           'max_score': max_score,
                           'sugestions': sugestions}
                request.session.clear()

                return render(request, self.result_template_name, context)
            else:
                request.session['current_page'] -= 1

        questions = self._get_context_question_list(page_question_list, request.session)

        is_last_page = request.session['current_page_no'] == request.session['last_page_no']

        context = {'quiz_id': quiz_id,
                   'is_last_page': is_last_page,
                   'current_page': request.session['current_page_no'],
                   'questions': questions,
                   'error': error}

        return render(request, self.template_name, context)

    def __call__(self, request, quiz_id):
        # if the session is new get all questions from DB and map them into a dict structure
        if request.session.get('quiz_id', -1) != quiz_id:
            self._init_session(request, quiz_id)

        question_list = request.session['question_list']

        # calculate current page
        delta_quesiton_list = request.session['current_page_no'] * self.questions_per_page
        page_question_list = question_list[delta_quesiton_list:
                                           (delta_quesiton_list + self.questions_per_page)]

        if request.method == 'POST':
            return self._handle_post_request(request, page_question_list, quiz_id)
        else:
            return self._handle_get_request(request, question_list, page_question_list, quiz_id)


quiz_view = QuizView()
