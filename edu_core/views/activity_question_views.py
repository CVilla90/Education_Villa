# Portfolio\Education_Villa\edu_core\views\activity_question_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import F, Q, Max
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.forms import formset_factory
from ..models import Activity, ActivityQuestion, Question, Option, Course
from ..forms import MCQForm, OptionFormSet, ContentBlockForm, OptionForm
import json
from .helper_functions import update_page_numbers, correct_question_order
import csv
import io
import logging

@login_required
def add_mcq(request, activity_id):
    """
    Add a multiple-choice question to an activity.
    """
    # Fetch the activity and related objects
    activity = get_object_or_404(Activity, id=activity_id)
    lesson = activity.lesson
    course = lesson.course

    insert_after_order = int(request.GET.get('insert_after', 0))

    OptionFormSet = formset_factory(OptionForm, extra=0, min_num=2, validate_min=True)

    if request.method == 'POST':
        mcq_form = MCQForm(request.POST)
        option_formset = OptionFormSet(request.POST, prefix='form')

        # Validate the forms before saving
        if mcq_form.is_valid() and option_formset.is_valid():
            correct_option = request.POST.get('correct_option')
            min_options_filled = sum(1 for form in option_formset if form.cleaned_data.get('text')) >= 2

            # Validate that the correct option is valid and corresponds to a non-empty option
            valid_options = False
            if correct_option is not None and correct_option.isdigit():
                idx = int(correct_option)
                if 0 <= idx < len(option_formset.forms):
                    selected_form = option_formset.forms[idx]
                    if selected_form.cleaned_data.get('text'):
                        valid_options = True

            # Save the question and related options if valid
            if valid_options and min_options_filled:
                question = mcq_form.save(commit=False)
                question.question_type = Question.MULTIPLE_CHOICE
                question.course = course
                question.save()

                # Add the question to the bank if indicated
                if mcq_form.cleaned_data.get('add_to_bank', True):
                    question.in_bank = True
                    question.save()

                # Save the activity question and reorder
                with transaction.atomic():
                    # Adjust orders for existing questions to make room for the new one
                    ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + 1000)
                    previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
                    page_number = previous_question.page_number if previous_question else 1

                    activity_question = ActivityQuestion.objects.create(
                        activity=activity,
                        question=question,
                        order=insert_after_order + 1,
                        page_number=page_number
                    )

                    # Reorder questions after inserting
                    correct_question_order(activity)

                # Save each option for the question
                for idx, option_form in enumerate(option_formset):
                    if option_form.cleaned_data.get('text'):
                        option = option_form.save(commit=False)
                        option.question = question
                        option.is_correct = (str(idx) == correct_option)  # Mark the correct option
                        option.save()

                messages.success(request, 'MCQ successfully added to the activity.')
                return redirect('edit_activity', activity_id=activity.id)

            # Add error messages if validation fails
            if not min_options_filled:
                mcq_form.add_error(None, "At least two options are required.")
            if not valid_options:
                mcq_form.add_error(None, "You must select one correct answer.")

        else:
            messages.error(request, "There was an error adding the MCQ. Please review the form.")
    else:
        mcq_form = MCQForm()
        option_formset = OptionFormSet(prefix='form')

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {
        'mcq_form': mcq_form,
        'option_formset': option_formset,
        'activity': activity
    })


@login_required
def add_content_block(request, activity_id):
    """
    Add a content block to an activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    insert_after_order = int(request.GET.get('insert_after', 0))

    if request.method == 'POST':
        form = ContentBlockForm(request.POST, request.FILES)
        if form.is_valid():
            content_block = form.save(commit=False)
            content_block.question_type = Question.CONTENT_BLOCK
            content_block.course = activity.lesson.course
            content_block.in_bank = form.cleaned_data.get('in_bank', False)
            content_block.save()

            # Add the content block to the activity and reorder questions
            with transaction.atomic():
                ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + 1000)
                previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
                page_number = previous_question.page_number if previous_question else 1

                ActivityQuestion.objects.create(
                    activity=activity,
                    question=content_block,
                    order=insert_after_order + 1,
                    page_number=page_number
                )

                # Reorder questions after insertion
                correct_question_order(activity)

            return redirect('edit_activity', activity_id=activity_id)
    else:
        form = ContentBlockForm()

    return render(request, 'edu_core/activity/forms/cb_creator.html', {'activity': activity, 'form': form})


@require_POST
@login_required
def add_question_to_activity(request, activity_id):
    """
    Add an existing question from the question bank to the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    question_id = request.POST.get('question_id')
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        new_order = insert_after_order + 1 if insert_after_order else 1

        # Adjust orders for existing questions
        ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).update(order=F('order') + 1)

        # Get the page number for the new question
        previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
        page_number = previous_question.page_number if previous_question else 1

        # Create the new ActivityQuestion instance
        ActivityQuestion.objects.create(
            activity=activity,
            question_id=question_id,
            order=new_order,
            page_number=page_number,
            is_separator=False
        )

        correct_question_order(activity)

    return redirect('edit_activity', activity_id=activity.id)


@login_required
def select_from_bank(request, activity_id):
    """
    Select questions from the question bank to add to the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    course = activity.lesson.course
    query = request.GET.get('q', '')
    insert_after_order = int(request.GET.get('insert_after', 0))

    # Fetch all questions from the bank
    questions = Question.objects.filter(course=course, in_bank=True)

    # Get IDs of questions already in the activity to avoid duplicates
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

            # Reorder questions after insertion
            correct_question_order(activity)

        return redirect('edit_activity', activity_id=activity.id)

    return render(request, 'edu_core/activity/views/select_from_bank.html', {
        'activity': activity,
        'questions': questions,
        'query': query,
        'existing_question_ids': existing_question_ids,
    })


@login_required
def question_type_selection(request, activity_id):
    """
    Allow the user to select the type of question to add.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'activity': activity})


@require_POST
@login_required
def reorder_questions(request, activity_id):
    """
    Reorder questions within the activity.
    """
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

                # Assign temporary high order to avoid UNIQUE constraint violation
                max_order = ActivityQuestion.objects.filter(activity=activity).aggregate(Max('order'))['order__max'] or 0
                temp_order = max_order + 1000
                question.order = temp_order
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

                # Assign temporary high order to avoid UNIQUE constraint violation
                temp_order = last_order + 1000
                question.order = temp_order
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
            page_to_remove = ActivityQuestion.objects.filter(activity=activity, is_separator=True, page_number=remove_page_number).first()
            if page_to_remove:
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
@login_required
def add_page(request, activity_id):
    """
    Add a new page separator within the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    insert_after_order = int(request.POST.get('insert_after', 0))

    # Prevent adding a page at the very beginning
    if insert_after_order == 0:
        messages.error(request, 'Cannot add a page at the very beginning. The activity already starts on Page 1.')
        return redirect('edit_activity', activity_id=activity.id)

    with transaction.atomic():
        new_order = insert_after_order + 1

        # Shift orders in reverse to avoid uniqueness constraint violation
        questions_to_shift = ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).order_by('-order')
        for aq in questions_to_shift:
            aq.order += 1
            aq.save()

        # Determine the page number for the new page separator
        previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
        page_number = previous_question.page_number + 1 if previous_question else 1

        # Create the new page separator
        ActivityQuestion.objects.create(
            activity=activity,
            order=new_order,
            page_number=page_number,
            is_separator=True
        )

        # Update page numbers for questions after the new page
        following_questions = ActivityQuestion.objects.filter(activity=activity, order__gt=new_order).order_by('order')
        for aq in following_questions:
            aq.page_number += 1
            aq.save()

    return redirect('edit_activity', activity_id=activity.id)

@require_POST
@login_required
def move_question(request, activity_id, direction):
    """
    Move a question up or down within the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
    except json.JSONDecodeError:
        question_id = None

    if question_id:
        with transaction.atomic():
            question = get_object_or_404(ActivityQuestion, id=question_id, activity=activity)
            original_order = question.order

            # Calculate max_order to be used for temp_order
            max_order = ActivityQuestion.objects.filter(activity=activity).aggregate(Max('order'))['order__max'] or 0
            temp_order = max_order + 1000  # Assign temporary high order to avoid conflicts

            if direction == 'up' and original_order > 1:
                swap_order = original_order - 1
            elif direction == 'down':
                if original_order < max_order:
                    swap_order = original_order + 1
                else:
                    return JsonResponse({'success': False})
            else:
                return JsonResponse({'success': False})

            swap_question = ActivityQuestion.objects.get(activity=activity, order=swap_order)

            # Assign temporary high order to 'question' to avoid conflict
            question.order = temp_order
            question.save(update_fields=['order'])

            # Set 'swap_question' to 'question's original order
            swap_question.order = original_order
            swap_question.save(update_fields=['order'])

            # Set 'question' to 'swap_order'
            question.order = swap_order
            question.save(update_fields=['order'])

            update_page_numbers(activity)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@require_POST
@login_required
def move_question_up(request, activity_id):
    return move_question(request, activity_id, 'up')

@require_POST
@login_required
def move_question_down(request, activity_id):
    return move_question(request, activity_id, 'down')

@require_POST
@login_required
def remove_question(request, activity_id):
    """
    Remove a question from the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
    except json.JSONDecodeError:
        question_id = None

    if question_id:
        with transaction.atomic():
            question_to_remove = get_object_or_404(ActivityQuestion, id=question_id, activity=activity)
            question_to_remove.delete()
            correct_question_order(activity)
            update_page_numbers(activity)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@require_POST
@login_required
def remove_page(request, activity_id):
    """
    Remove a page separator from the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    try:
        data = json.loads(request.body)
        page_number = data.get('page_number')
    except json.JSONDecodeError:
        page_number = None

    if page_number:
        with transaction.atomic():
            page_to_remove = ActivityQuestion.objects.filter(activity=activity, is_separator=True, page_number=page_number).first()
            if page_to_remove:
                page_to_remove.delete()
                following_questions = ActivityQuestion.objects.filter(activity=activity, page_number__gt=page_number)
                for aq in following_questions:
                    aq.page_number -= 1
                    aq.save()
                correct_question_order(activity)
                update_page_numbers(activity)
                return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# Set up logging
logger = logging.getLogger(__name__)

@login_required
def mcq_parser(request, course_id=None, activity_id=None):
    """
    View to handle MCQ parsing from text input.
    """
    course = None
    activity = None

    if course_id:
        course = get_object_or_404(Course, id=course_id)
    elif activity_id:
        activity = get_object_or_404(Activity, id=activity_id)
        course = activity.lesson.course  # Set course based on activity

    if request.method == 'POST':
        # Get the input from the form
        csv_input = request.POST.get('csv_input')

        if not csv_input:
            messages.error(request, "No input provided.")
            if activity:
                return redirect('activity_mcq_parser', activity_id=activity_id)
            elif course:
                return redirect('course_mcq_parser', course_id=course_id)

        rows = csv_input.splitlines()

        # Determine the starting order value for new questions in the activity
        if activity:
            last_question = ActivityQuestion.objects.filter(activity=activity).order_by('-order').first()
            next_order = last_question.order + 1 if last_question else 1
        else:
            next_order = None  # No order needed for questions in the question bank

        # Process each row and create questions
        for idx, row in enumerate(rows, start=1):
            try:
                # Parse CSV row into components
                fields = next(csv.reader([row]))
                if len(fields) < 6:
                    raise ValueError("Row does not have enough fields.")

                # Extract question fields from the parsed CSV
                question_type, key_name, text, *options = fields

                if question_type != 'MCQ':
                    raise ValueError(f"Unsupported question type '{question_type}'.")

                # Extract feedback (last field)
                feedback = options[-1]
                options = options[:-1]  # Remove feedback from options

                # Parse options and their correctness
                parsed_options = []
                for i in range(0, len(options) - 2, 2):
                    option_text = options[i]
                    is_correct = options[i + 1].strip().lower() == 'true'
                    parsed_options.append((option_text, is_correct))

                if len(parsed_options) < 2:
                    raise ValueError("MCQ must have at least two options.")

                randomize_options = options[-2].strip().lower() == 'true'
                add_to_bank = options[-1].strip().lower() == 'true'

                # Create question
                question = Question.objects.create(
                    course=course,  # Set course based on the context
                    question_type=Question.MULTIPLE_CHOICE,
                    key_name=key_name,
                    text=text,
                    randomize_options=randomize_options,
                    in_bank=add_to_bank,
                    feedback=feedback,  # Set the feedback field
                )

                # Save options
                for option_text, is_correct in parsed_options:
                    Option.objects.create(question=question, text=option_text, is_correct=is_correct)

                # If linked to an activity, create ActivityQuestion and assign order
                if activity:
                    ActivityQuestion.objects.create(
                        activity=activity,
                        question=question,
                        order=next_order,
                    )
                    next_order += 1  # Increment order for the next question

            except Exception as e:
                messages.error(request, f"Exception in row {idx}: {str(e)}")
                continue

        if activity:
            return redirect('edit_activity', activity_id=activity_id)
        elif course:
            return redirect('question_bank', course_id=course_id)

    # Handle GET request to render the parser form
    return render(request, 'edu_core/activity/views/mcq_parser.html', {
        'activity': activity,
        'course': course
    })
