# Portfolio\Education_Villa\edu_core\views\question_bank_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from ..models import Question, Course, Option
from ..forms import QuestionBankForm, MCQForm, ContentBlockForm
from django.db.models import Q

@login_required
def question_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    query = request.GET.get('q', '')
    questions = Question.objects.filter(course=course, in_bank=True)
    
    if query:
        questions = questions.filter(
            Q(key_name__icontains=query) | Q(text__icontains=query)
        )

    return render(request, 'edu_core/question_bank/question_bank.html', {'course': course, 'questions': questions})

@login_required
def add_question_to_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = QuestionBankForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.course = course
            question.in_bank = True
            question.save()
            return redirect('question_bank', course_id=course.id)
    else:
        form = QuestionBankForm()
    return render(request, 'edu_core/question_bank/add_question_to_bank.html', {'form': form, 'course': course})

@login_required
def edit_question_in_bank(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    course = question.course  # Retrieve the course for redirection and context

    if question.question_type == Question.MULTIPLE_CHOICE:
        return edit_mcq_question(request, question, course)
    elif question.question_type == Question.CONTENT_BLOCK:
        return edit_content_block(request, question, course)
    else:
        # Handle other question types or render a generic form
        return edit_generic_question(request, question, course)

def edit_mcq_question(request, question, course):
    if request.method == 'POST':
        form = MCQForm(request.POST)
        if form.is_valid():
            # Update the question fields
            question.text = form.cleaned_data['question_text']
            question.key_name = form.cleaned_data['key_name']
            question.correct_answer = form.cleaned_data['correct_answer']
            question.randomize_options = form.cleaned_data.get('randomize_options', False)
            question.save()

            # Update the options
            # First, delete existing options
            Option.objects.filter(question=question).delete()

            # Create new options
            for option_number in range(1, 5):
                option_text = form.cleaned_data.get(f'option_{option_number}')
                if option_text:
                    Option.objects.create(
                        question=question,
                        text=option_text,
                        is_correct=(f'option_{option_number}' == form.cleaned_data['correct_answer'])
                    )

            return redirect('question_bank', course_id=course.id)
    else:
        # Prepare initial data for the form
        initial_data = {
            'key_name': question.key_name,
            'question_text': question.text,
            'randomize_options': question.randomize_options,
            'add_to_bank': question.in_bank,  # Assuming you want to allow changing this
        }

        # Retrieve existing options
        options = list(question.options.all())
        for idx, option in enumerate(options, start=1):
            initial_data[f'option_{idx}'] = option.text
            if option.is_correct:
                initial_data['correct_answer'] = f'option_{idx}'

        form = MCQForm(initial=initial_data)

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {'form': form, 'course': course, 'editing': True,'question': question})


def edit_content_block(request, question, course):
    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            content_block = form.save(commit=False)
            content_block.in_bank = form.cleaned_data.get('in_bank', False)
            content_block.save()
            return redirect('question_bank', course_id=course.id)
    else:
        form = ContentBlockForm(instance=question)
    return render(request, 'edu_core/activity/forms/cb_creator.html', {'form': form, 'course': course, 'editing': True, 'question': question})


def edit_generic_question(request, question, course):
    if request.method == 'POST':
        form = QuestionBankForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('question_bank', course_id=course.id)
    else:
        form = QuestionBankForm(instance=question)

    return render(request, 'edu_core/question_bank/edit_question_in_bank.html', {'form': form, 'course': course, 'question': question})


@login_required
def question_type_selection_for_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'course': course})

@login_required
def add_mcq_to_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = MCQForm(request.POST)
        if form.is_valid():
            # Create the question without an activity
            question = Question.objects.create(
                text=form.cleaned_data['question_text'],
                question_type=Question.MULTIPLE_CHOICE,
                correct_answer=form.cleaned_data['correct_answer'],
                randomize_options=form.cleaned_data.get('randomize_options', False),
                key_name=form.cleaned_data.get('key_name', ''),
                course=course,  # Automatically relate the course
                in_bank=True  # Mark it as part of the bank
            )

            # Create options for the question
            for option_number in range(1, 5):
                option_text = form.cleaned_data.get(f'option_{option_number}')
                if option_text:
                    Option.objects.create(
                        question=question,
                        text=option_text,
                        is_correct=(f'option_{option_number}' == form.cleaned_data['correct_answer'])
                    )

            return redirect('question_bank', course_id=course.id)
    else:
        form = MCQForm()

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {'form': form, 'course': course})

@login_required
def add_content_block_to_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES)
        if form.is_valid():
            content_block = form.save(commit=False)
            content_block.course = course
            content_block.question_type = Question.CONTENT_BLOCK
            content_block.in_bank = form.cleaned_data.get('in_bank', False)
            content_block.save()
            return redirect('question_bank', course_id=course.id)
    else:
        form = ContentBlockForm()

    return render(request, 'edu_core/activity/forms/cb_creator.html', {
        'form': form,
        'course': course,
        'editing': False,
        'question': None
    })

