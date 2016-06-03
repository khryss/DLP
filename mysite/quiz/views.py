from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from .models import Quiz, Question, Option

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def index_view(request):
    template_name = 'index.html'

    return render(request, template_name, {'quizs_list': Quiz.objects.all})


def get_question_mapping(question_list):
    '''
    Maps the questions from DB into 2 structures:
      question_mapping - keeps the questions and options text
      selected_option - keeps the option select info for the session

    questions_mapping = [{'question_text': 'text',
                          'options': {'option_1': 'text',
                                      'option_2': 'text'}},
                         {'question_text': 'text',
                          'options': {'option_3': 'text'}}]
    selected_options = {'option_1': False,
                        'option_2': True}}
    '''
    selected_options = {}
    questions_mapping = []

    for question in question_list:
        raw_options = question.option_set.all()

        mapped_options = {}
        for option in raw_options:
            mapped_options['option_' + str(option.id)] = option.text

            selected_options['option_' + str(option.id)] = False

        questions_mapping.append({'question_text': question.text,
                                  'options': mapped_options})

    return questions_mapping, selected_options


def quiz_view(request, quiz_id):
    template_name = 'quiz_form.html'
    result_template_name = 'quiz_result.html'
    questions_per_page = 2

    # if the session is new get all questions from DB and map them into a dict structure
    if request.session.get('quiz_id', -1) != quiz_id:
        raw_question_list = Question.objects.filter(quiz=quiz_id).prefetch_related('option_set')

        request.session.clear()
        request.session['quiz_id'] = quiz_id
        request.session['current_page_no'] = 0

        # 'selected_options' keeps track of selected options for each session
        request.session['question_list'], request.session['selected_options'] = \
            get_question_mapping(raw_question_list)

        request.session['last_page_no'] = \
            len(request.session['question_list']) / questions_per_page

    question_list = request.session['question_list']

    # calculate current page
    delta_quesiton_list = request.session['current_page_no'] * questions_per_page
    page_question_list = question_list[delta_quesiton_list :
                                       (delta_quesiton_list + questions_per_page)]

    if request.method == 'POST':
        def _validate_min_options_selected(question_list, selected_options):
            for question in question_list:
                for option_id, _ in question['options'].items():
                    if selected_options[option_id]:
                        break
                else:
                    raise ValidationError('Please fill all questions '
                                          'with at least one option!')

        # update the session data with selected options from POST
        for question in page_question_list:
            for option_id, _ in question['options'].items():
                request.session['selected_options'][option_id] = (option_id in request.POST)

        if 'Previous' in request.POST:
            request.session['current_page_no'] -= 1
        elif 'Next' in request.POST or \
             'Finish' in request.POST:
            try:
                _validate_min_options_selected(page_question_list,
                                               request.session['selected_options'])
            except ValidationError as exception:
                request.session['error'] = exception.message
            else:
                request.session['current_page_no'] += 1

        return redirect('quiz', quiz_id=quiz_id)


    else:
        def _get_context_question_list(page_question_list, request_session):
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
                    is_selected = request_session['selected_options'][option_id]
                    options.append((option_id, option_text, is_selected))

                context_question_list.append((question['question_text'], options))
            return context_question_list

        error = request.session.get('error', None)
        request.session['error'] = None
        if request.session['current_page_no'] > request.session['last_page_no']:
            if not error:
                request.session.clear()

                context = {}
                return render(request, result_template_name, context)
            else:
                request.session['current_page'] -= 1

        questions = _get_context_question_list(page_question_list, request.session)

        context = {'quiz_id': quiz_id,
                   'is_last_page': request.session['current_page_no'] == request.session['last_page_no'],
                   'current_page': request.session['current_page_no'],
                   'questions': questions,
                   'error': error}

        return render(request, template_name, context)
