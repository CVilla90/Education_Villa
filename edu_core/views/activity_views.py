from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.db import transaction
from django.db.models import F, Q, Max
from ..models import Activity, ActivityQuestion, Grade, Lesson, Option, Question
from ..forms import ActivityForm, MCQForm, ContentBlockForm
import random
import json

# Helper functions
def update_page_numbers(activity):
    """
    Update page numbers for all activity questions based on their order.
    """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    current_page_number = 1
    for aq in activity_questions:
        if aq.is_separator:
            current_page_number += 1
        aq.page_number = current_page_number
        aq.save()

def correct_question_order(activity):
    """
    Ensure that the order of questions is sequential and correct.
    """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    expected_order = 1
    with transaction.atomic():
        for aq in activity_questions:
            if aq.order != expected_order:
                aq.order = expected_order
                aq.save()
            expected_order += 1

@login_required
def activity_add(request, lesson_id):
    """
    Add a new activity to a lesson.
    """
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
    """
    Delete an existing activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)

    if request.user == activity.lesson.course.author or request.user.is_superuser:
        activity.delete()
        messages.success(request, 'The activity has been successfully deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this activity.')

    return redirect('lesson_view', lesson_id=activity.lesson.id)

@never_cache
@login_required
def activity_view(request, activity_id):
    """
    View an activity, handle pagination, answer submission, and grading.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    current_date = timezone.now().date()

    # Check if the activity is available
    if (activity.start_date and current_date < activity.start_date) or (activity.end_date and current_date > activity.end_date):
        messages.error(request, 'This activity is not available at this time.')
        return redirect('lesson_view', lesson_id=activity.lesson.id)

    # Fetch all questions and handle pagination
    activity_questions = ActivityQuestion.objects.filter(activity=activity).select_related('question').order_by('order')
    total_pages = activity_questions.aggregate(Max('page_number'))['page_number__max'] or 1
    page = int(request.GET.get('page', 1))
    questions_on_page = activity_questions.filter(page_number=page, is_separator=False, question__isnull=False)

    # Initialize session answers if not present
    if 'answers' not in request.session:
        request.session['answers'] = {}

    # Handle form submission
    if request.method == 'POST':
        # Handle retry button to reset session and redirect to the first page
        if 'retry' in request.POST:
            request.session['answers'] = {}
            request.session.modified = True  # Ensure the session is saved
            return redirect(f"{request.path}?page=1")

        # Store answers in session when navigating pages
        for aq in questions_on_page:
            question = aq.question
            if question and question.question_type == Question.MULTIPLE_CHOICE:
                submitted_option_id = request.POST.get(f'question_{question.id}')
                if submitted_option_id:
                    request.session['answers'][str(question.id)] = submitted_option_id
                    request.session.modified = True  # Mark session as modified

        # Handle navigation between pages
        if 'next_page' in request.POST and page < total_pages:
            return redirect(f"{request.path}?page={page + 1}")
        elif 'previous_page' in request.POST and page > 1:
            return redirect(f"{request.path}?page={page - 1}")

        # Final submission: grade the answers
        if 'submit_final' in request.POST:
            answers = request.session.get('answers', {})
            graded_questions = activity_questions.filter(question__question_type=Question.MULTIPLE_CHOICE)
            score = 0
            total_questions = graded_questions.count()  # Count only gradeable questions
            results = {}

            for aq in graded_questions:
                question = aq.question
                if question:
                    submitted_option_id = answers.get(str(question.id))
                    correct_option = question.options.filter(is_correct=True).first()
                    if submitted_option_id:
                        submitted_option = Option.objects.filter(id=submitted_option_id).first()
                        is_correct = submitted_option.is_correct if submitted_option else False
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

            # Save grade and clear session answers
            Grade.objects.create(
                student=request.user,
                activity=activity,
                score=percentage_score
            )
            request.session['answers'] = {}  # Clear session answers after grading

            return render(request, 'edu_core/activity/activity_view.html', {
                'activity': activity,
                'activity_questions': activity_questions,
                'results': results,
                'score': score,
                'total_questions': total_questions,
                'percentage_score': percentage_score,
                'grade_history': Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at'),
                'total_pages': total_pages,
                'current_page': page,
                'questions_on_page': questions_on_page,
            })

    # Shuffle options if necessary and load them into context
    for aq in questions_on_page:
        question = aq.question
        if question and question.question_type == Question.MULTIPLE_CHOICE:
            options = list(question.options.all())
            if question.randomize_options:
                random.shuffle(options)
            question.shuffled_options = options

    # Pass session answers as a JSON string safely to the template
    answers_json = json.dumps(request.session.get('answers', {}))  # Ensure it's a proper JSON string

    return render(request, 'edu_core/activity/activity_view.html', {
        'activity': activity,
        'activity_questions': activity_questions,
        'grade_history': Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at'),
        'total_pages': total_pages,
        'current_page': page,
        'questions_on_page': questions_on_page,
        'answers_json': answers_json,  # Pass the safe JSON string to the template
    })

@login_required
def add_mcq(request, activity_id):
    """
    Add a multiple-choice question to an activity.
    """
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

                ActivityQuestion.objects.create(
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

            return redirect('edit_activity', activity_id=activity.id)
    else:
        form = MCQForm()

    return render(request, 'edu_core/activity/forms/mcq_creator.html', {'form': form, 'activity': activity})

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

            # Handle reordering and insertion within a transaction
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

                questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
                for idx, aq in enumerate(questions_to_reorder):
                    aq.order = idx + 1
                    aq.save()

            return redirect('edit_activity', activity_id=activity_id)
    else:
        form = ContentBlockForm()

    return render(request, 'edu_core/activity/forms/cb_creator.html', {'activity': activity, 'form': form})

@csrf_exempt
def upload_image(request):
    """
    Handle image uploads for the content editor.
    """
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        path = default_storage.save('uploads/' + image.name, ContentFile(image.read()))
        full_url = request.build_absolute_uri(default_storage.url(path))
        return JsonResponse({'url': full_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

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
    """
    Allow the user to select the type of question to add.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    return render(request, 'edu_core/activity/views/question_type_selection.html', {'activity': activity})

@login_required
def edit_activity(request, activity_id):
    """
    Edit an existing activity, including reordering questions.
    """
    activity = get_object_or_404(Activity, id=activity_id)

    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            return redirect('lesson_view', lesson_id=activity.lesson.id)
    else:
        form = ActivityForm(instance=activity)

    # Fetch all activity questions including content blocks
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')

    return render(request, 'edu_core/activity/activity_edit.html', {
        'activity': activity,
        'form': form,
        'activity_questions': activity_questions,
    })

@require_POST
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
def add_question_to_activity(request, activity_id):
    """
    Add an existing question to the activity.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    question_id = request.POST.get('question_id')
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        new_order = insert_after_order + 1 if insert_after_order else 1

        ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).update(order=F('order') + 1)

        page_number = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first().page_number

        ActivityQuestion.objects.create(
            activity=activity,
            question_id=question_id,
            order=new_order,
            page_number=page_number,
            is_separator=False
        )

        update_page_numbers(activity)

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
    """
    API endpoint to move a question up.
    """
    return move_question(request, activity_id, 'up')

@require_POST
@login_required
def move_question_down(request, activity_id):
    """
    API endpoint to move a question down.
    """
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
