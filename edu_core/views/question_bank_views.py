# Portfolio\Education_Villa\edu_core\views\question_bank_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from ..models import Question, Course, Option
from ..forms import QuestionBankForm, MCQForm
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
    
    if request.method == 'POST':
        form = QuestionBankForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('question_bank', course_id=question.course.id)
    else:
        form = QuestionBankForm(instance=question)
    
    # Since the course should not be changed, explicitly set it in the context if needed
    context = {
        'form': form,
        'question': question,
    }
    
    return render(request, 'edu_core/question_bank/edit_question_in_bank.html', context)

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
