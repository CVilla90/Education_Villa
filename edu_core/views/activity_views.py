# Portfolio\Education_Villa\edu_core\views\activity_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.db.models import F, Q, Max
from ..models import Activity, ActivityQuestion, Course, Grade, Lesson, Option, Question
from ..forms import ActivityForm, MCQForm
import random
import json

@login_required
def activity_add(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.lesson = lesson
            activity.save()
            return redirect('lesson_view', lesson_id=lesson.id)
    else:
        form = ActivityForm()
    return render(request, 'edu_core/activity/activity_add.html', {'form': form, 'lesson': lesson})

@login_required
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    
    if request.user == activity.lesson.course.author or request.user.is_superuser:
        activity.delete()
        messages.success(request, 'The activity has been successfully deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this activity.')

    return redirect('lesson_view', lesson_id=activity.lesson.id)

@login_required
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    current_date = timezone.now().date()
    
    if (activity.start_date and current_date < activity.start_date) or (activity.end_date and current_date > activity.end_date):
        messages.error(request, 'This activity is not available at this time.')
        return redirect('lesson_view', lesson_id=activity.lesson.id)

    activity_questions = ActivityQuestion.objects.filter(activity=activity).select_related('question').order_by('order')
    total_pages = activity_questions.aggregate(Max('page_number'))['page_number__max'] or 1
    page = int(request.GET.get('page', 1))

    questions_on_page = activity_questions.filter(page_number=page).exclude(question__isnull=True)
    
    grade_history = Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at')

    if request.method == 'POST' and 'retry' not in request.POST:
        score = 0
        total_questions = questions_on_page.count()
        results = {}

        for aq in questions_on_page:
            question = aq.question
            submitted_option_id = request.POST.get(f'question_{question.id}')
            correct_option = question.options.filter(is_correct=True).first()
            if submitted_option_id:
                submitted_option = Option.objects.get(id=submitted_option_id)
                is_correct = submitted_option.is_correct
                results[question.id] = {
                    'correct': is_correct,
                    'submitted_option': submitted_option,
                    'correct_option': correct_option
                }
                if is_correct:
                    score += 1
            else:
                results[question.id] = {
                    'correct': False,
                    'submitted_option': None,
                    'correct_option': correct_option
                }

        percentage_score = (score / total_questions) * 100 if total_questions > 0 else 0

        Grade.objects.create(
            student=request.user,
            activity=activity,
            score=percentage_score
        )

        return render(request, 'edu_core/activity/activity_view.html', {
            'activity': activity,
            'activity_questions': activity_questions,
            'results': results,
            'score': score,
            'total_questions': total_questions,
            'percentage_score': percentage_score,
            'grade_history': grade_history,
            'total_pages': total_pages,
            'current_page': page,
            'questions_on_page': questions_on_page,
        })

    else:
        for aq in questions_on_page:
            question = aq.question
            options = list(question.options.all())
            if question.randomize_options:
                random.shuffle(options)
            question.shuffled_options = options

        return render(request, 'edu_core/activity/activity_view.html', {
            'activity': activity,
            'activity_questions': activity_questions,
            'grade_history': grade_history,
            'total_pages': total_pages,
            'current_page': page,
            'questions_on_page': questions_on_page,
        })

@login_required
def add_mcq(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    lesson = activity.lesson
    course = lesson.course

    insert_after_order = int(request.GET.get('insert_after', 0))

    if request.method == 'POST':
        form = MCQForm(request.POST)
        if form.is_valid():
            question = Question.objects.create(
                text=form.cleaned_data['question_text'],
                question_type=Question.MULTIPLE_CHOICE,
                correct_answer=form.cleaned_data['correct_answer'],
                randomize_options=form.cleaned_data.get('randomize_options', False),
                key_name=form.cleaned_data.get('key_name', ''),
                course=course
            )

            if form.cleaned_data.get('add_to_bank', True):
                question.in_bank = True
                question.save()

            with transaction.atomic():
                ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + 1000)

                previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
                if previous_question:
                    page_number = previous_question.page_number
                else:
                    page_number = 1

                new_activity_question = ActivityQuestion.objects.create(
                    activity=activity,
                    question=question,
                    order=insert_after_order + 1,
                    page_number=page_number
                )

                questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
                for idx, aq in enumerate(questions_to_reorder):
                    aq.order = idx + 1
                    aq.save()

            for option_number in range(1, 5):
                option_text = form.cleaned_data.get(f'option_{option_number}')
                if option_text:
                    Option.objects.create(
                        question=question,
                        text=option_text,
                        is_correct=(f'option_{option_number}' == form.cleaned_data['correct_answer'])
                    )

            # Redirect to the edit activity template instead of the activity view
            return redirect('edit_activity', activity_id=activity.id)
    else:
        form = MCQForm()

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {'form': form, 'activity': activity})

@login_required
def select_from_bank(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course = activity.lesson.course
    query = request.GET.get('q', '')
    insert_after_order = int(request.GET.get('insert_after', 0))

    # Fetch all questions from the bank
    questions = Question.objects.filter(course=course, in_bank=True)

    # Get IDs of questions already in the activity
    existing_question_ids = ActivityQuestion.objects.filter(activity=activity).values_list('question_id', flat=True)

    # Apply search filter if a query is provided
    if query:
        questions = questions.filter(
            Q(key_name__icontains=query) | Q(text__icontains=query)
        )

    if request.method == 'POST':
        selected_question_ids = request.POST.getlist('selected_questions')
        
        # Handle addition of questions while avoiding duplicates
        with transaction.atomic():
            ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + len(selected_question_ids) + 1000)

            previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
            new_page_number = previous_question.page_number if previous_question else 1

            for i, question_id in enumerate(selected_question_ids):
                if int(question_id) not in existing_question_ids:
                    question = get_object_or_404(Question, id=question_id)
                    ActivityQuestion.objects.create(
                        activity=activity,
                        question=question,
                        order=insert_after_order + i + 1,
                        page_number=new_page_number
                    )

            questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
            for idx, aq in enumerate(questions_to_reorder):
                aq.order = idx + 1
                aq.save()

        return redirect('edit_activity', activity_id=activity.id)

    return render(request, 'edu_core/activity/views/select_from_bank.html', {
        'activity': activity,
        'questions': questions,
        'query': query,
        'existing_question_ids': existing_question_ids,
    })

@login_required
def question_type_selection(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'activity': activity})

@login_required
def edit_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    
    print(f"Activity ID: {activity_id}")
    print(f"Activity Name: {activity.name}")
    print(f"Start Date from DB: {activity.start_date}")
    print(f"End Date from DB: {activity.end_date}")

    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            print("Form is valid. Saving data...")
            form.save()
            return redirect('lesson_view', lesson_id=activity.lesson.id)
        else:
            print("Form is not valid. Errors:", form.errors)
    else:
        form = ActivityForm(instance=activity)
        print("Form initial data:")
        print(f"Start Date in Form: {form.initial.get('start_date')}")
        print(f"End Date in Form: {form.initial.get('end_date')}")

    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')

    return render(request, 'edu_core/activity/activity_edit.html', {
        'activity': activity,
        'form': form,
        'activity_questions': activity_questions,
    })

@require_POST
def reorder_questions(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)

    move_up_id = request.POST.get('move_up')
    move_down_id = request.POST.get('move_down')
    remove_question_id = request.POST.get('remove_question')
    remove_page_number = request.POST.get('remove_page')

    if move_up_id:
        with transaction.atomic():
            question = ActivityQuestion.objects.get(id=move_up_id, activity=activity)
            if question.order > 1:
                previous_question = ActivityQuestion.objects.get(activity=activity, order=question.order - 1)

                question.order = ActivityQuestion.objects.filter(activity=activity).count() + 1
                question.save()

                previous_question.order += 1
                previous_question.save()

                question.order = previous_question.order - 1
                question.save()

                update_page_numbers(activity)

    elif move_down_id:
        with transaction.atomic():
            question = ActivityQuestion.objects.get(id=move_down_id, activity=activity)
            last_order = ActivityQuestion.objects.filter(activity=activity).count()
            if question.order < last_order:
                next_question = ActivityQuestion.objects.get(activity=activity, order=question.order + 1)

                question.order = ActivityQuestion.objects.filter(activity=activity).count() + 1
                question.save()

                next_question.order -= 1
                next_question.save()

                question.order = next_question.order + 1
                question.save()

                update_page_numbers(activity)

    elif remove_question_id:
        with transaction.atomic():
            question_to_remove = ActivityQuestion.objects.get(id=remove_question_id, activity=activity)
            question_to_remove.delete()

            questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
            for idx, aq in enumerate(questions_to_reorder):
                aq.order = idx + 1
                aq.save()

            update_page_numbers(activity)

    elif remove_page_number:
        with transaction.atomic():
            page_to_remove = ActivityQuestion.objects.get(activity=activity, is_separator=True, page_number=remove_page_number)
            page_to_remove.delete()

            following_questions = ActivityQuestion.objects.filter(activity=activity, page_number__gt=remove_page_number).order_by('order')
            for aq in following_questions:
                aq.page_number -= 1
                aq.save()

            correct_question_order(activity)
            update_page_numbers(activity)

    correct_question_order(activity)

    return redirect('edit_activity', activity_id=activity.id)

@require_POST
def add_page(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        if insert_after_order == 0:
            new_order = 1
        else:
            new_order = insert_after_order + 1

        questions_to_shift = ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).order_by('-order')
        for question in questions_to_shift:
            question.order += 1
            question.save()

        previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
        if previous_question:
            page_number = previous_question.page_number + 1
        else:
            page_number = 1

        new_separator = ActivityQuestion.objects.create(
            activity=activity,
            order=new_order,
            page_number=page_number,
            is_separator=True
        )

        for question in ActivityQuestion.objects.filter(activity=activity, order__gt=new_order).order_by('order'):
            question.page_number += 1
            question.save()

    return redirect('edit_activity', activity_id=activity.id)

@require_POST
def add_question_to_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    question_id = request.POST.get('question_id')
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        if insert_after_order == 0:
            new_order = 1
        else:
            new_order = insert_after_order + 1

        questions_to_shift = ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).order_by('-order')
        for question in questions_to_shift:
            question.order += 1
            question.save()

        new_activity_question = ActivityQuestion.objects.create(
            activity=activity,
            question_id=question_id,
            order=new_order,
            page_number=ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first().page_number,
            is_separator=False
        )

        update_page_numbers(activity)

    return redirect('edit_activity', activity_id=activity.id)

def update_page_numbers(activity):
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    current_page_number = 1

    for aq in activity_questions:
        if aq.is_separator:
            current_page_number += 1
        aq.page_number = current_page_number
        aq.save()

def correct_question_order(activity):
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    expected_order = 1

    with transaction.atomic():
        for aq in activity_questions:
            if aq.order != expected_order:
                aq.order = expected_order
                aq.save()
            expected_order += 1
