# Portfolio\Education_Villa\edu_core\views\activity_viewing_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db.models import Max
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import json
import random

from ..models import Activity, ActivityQuestion, Question, Grade, Option, ActivityAttempt

@never_cache
@login_required
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    current_date = timezone.now().date()

    # Check if the activity is available within the specified date range
    if (activity.start_date and current_date < activity.start_date) or (activity.end_date and current_date > activity.end_date):
        messages.error(request, 'This activity is not available at this time.')
        return redirect('lesson_view', lesson_id=activity.lesson.id)

    # Count user attempts
    user_attempts = activity.attempts.filter(user=request.user).count()

    # Check if the user has exceeded the allowed attempts
    if not activity.unlimited_attempts and activity.max_attempts is not None and user_attempts >= activity.max_attempts:
        messages.error(request, 'You have reached the maximum number of attempts for this activity.')
        return redirect('lesson_view', lesson_id=activity.lesson.id)

    # If it's a new attempt, increment the attempts count
    if not request.session.get('reviewing', False):
        activity.attempts.create(user=request.user)

    # Fetch all questions and handle pagination
    activity_questions = ActivityQuestion.objects.filter(activity=activity, question__isnull=False).select_related('question').order_by('order')
    total_pages = activity_questions.aggregate(Max('page_number'))['page_number__max'] or 1
    page = int(request.GET.get('page', 1))
    questions_on_page = activity_questions.filter(page_number=page, is_separator=False, question__isnull=False)

    # Calculate question offset to keep question numbering continuous across pages
    question_offset = activity_questions.filter(page_number__lt=page).filter(is_separator=False, question__isnull=False).count()

    # Initialize session variables if not present
    request.session.setdefault('answers', {})
    request.session.setdefault('shuffled_options', {})

    # Initialize variables
    score = None
    percentage_score = None

    # Handle form submission
    if request.method == 'POST':
        if 'retry' in request.POST:
            return handle_retry(request)
        store_answers_in_session(request, questions_on_page)
        if 'next_page' in request.POST and page < total_pages:
            return redirect(f"{request.path}?page={page + 1}")
        elif 'previous_page' in request.POST and page > 1:
            return redirect(f"{request.path}?page={page - 1}")
        elif 'submit_final' in request.POST:
            return handle_final_submission(request, activity, activity_questions, total_pages, page, questions_on_page)

    # After handling POST, retrieve updated 'answers' from the session
    if request.session.get('reviewing', False):
        score = request.session.get('score')
        percentage_score = request.session.get('percentage_score')
        answers = request.session.get('review_answers', {})
    else:
        answers = request.session.get('answers', {})

    # Shuffle options if needed
    shuffle_options_if_needed(request, questions_on_page)

    answers_json = json.dumps(answers)

    return render(request, 'edu_core/activity/activity_view.html', {
        'activity': activity,
        'activity_questions': activity_questions,
        'grade_history': Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at'),
        'total_pages': total_pages,
        'current_page': page,
        'questions_on_page': questions_on_page,
        'answers_json': answers_json,
        'question_offset': question_offset,
        'score': score,
        'percentage_score': percentage_score,
        'total_questions': activity_questions.filter(is_separator=False, question__isnull=False, question__question_type=Question.MULTIPLE_CHOICE).count(),
        'answers': answers,  # Ensure answers are passed
        'user_attempts': user_attempts,
    })


def handle_retry(request):
    request.session['answers'] = {}
    request.session['review_answers'] = {}
    request.session['reviewing'] = False
    request.session['score'] = None
    request.session['percentage_score'] = None
    request.session['shuffled_options'] = {}  # Reset shuffled options
    request.session.modified = True
    return redirect(f"{request.path}?page=1")

def store_answers_in_session(request, questions_on_page):
    """
    Store answers in the session when navigating between pages.
    Only update the answers when a new selection is made.
    """
    for aq in questions_on_page:
        question = aq.question
        if question and question.question_type == Question.MULTIPLE_CHOICE:
            submitted_option_id = request.POST.get(f'question_{question.id}')
            if submitted_option_id is not None:
                # Update the answer if a new selection is made
                request.session['answers'][str(question.id)] = submitted_option_id
                request.session.modified = True
            # Do not remove previous answers if no new selection is made

def handle_final_submission(request, activity, activity_questions, total_pages, page, questions_on_page):
    answers = request.session.get('answers', {}).copy()

    # Filter out questions that are not separators and ensure question is not None
    graded_questions = activity_questions.filter(
        is_separator=False,
        question__isnull=False,
        question__question_type=Question.MULTIPLE_CHOICE
    )

    score, results = calculate_grade(graded_questions, answers)
    total_questions = graded_questions.count()
    percentage_score = (score / total_questions) * 100 if total_questions else 0

    Grade.objects.create(student=request.user, activity=activity, score=percentage_score)

    # Store results in session for reviewing
    request.session['review_answers'] = answers
    request.session['score'] = score
    request.session['percentage_score'] = percentage_score
    request.session['reviewing'] = True
    request.session['answers'] = {}  # Clear current answers
    request.session.modified = True

    # Shuffle options for rendering
    shuffle_options_if_needed(request, questions_on_page)

    # Calculate question offset for continuous numbering
    question_offset = sum([len(activity_questions.filter(page_number=i)) for i in range(1, page)])

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
        'question_offset': question_offset,
        'answers_json': json.dumps(answers),
        'answers': answers,  # Ensure answers are passed
    })

def calculate_grade(graded_questions, answers):
    score = 0
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

    return score, results

def shuffle_options_if_needed(request, questions_on_page):
    request.session.setdefault('shuffled_options', {})
    for aq in questions_on_page:
        question = aq.question
        if question and question.question_type == Question.MULTIPLE_CHOICE:
            question_id_str = str(question.id)
            if question.randomize_options:
                if question_id_str not in request.session['shuffled_options']:
                    options = list(question.options.all())
                    random.shuffle(options)
                    option_ids = [option.id for option in options]
                    request.session['shuffled_options'][question_id_str] = option_ids
                    request.session.modified = True
                else:
                    option_ids = request.session['shuffled_options'][question_id_str]
                    options = list(Option.objects.filter(id__in=option_ids))
                    options.sort(key=lambda x: option_ids.index(x.id))
            else:
                options = list(question.options.all())
                request.session['shuffled_options'][question_id_str] = [option.id for option in options]
            question.shuffled_options = options

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        path = default_storage.save('uploads/' + image.name, ContentFile(image.read()))
        full_url = request.build_absolute_uri(default_storage.url(path))
        return JsonResponse({'url': full_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)
