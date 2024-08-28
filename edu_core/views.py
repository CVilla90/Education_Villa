# Portfolio\Education_Villa\edu_core\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views import generic
from django.db import transaction
from django.db.models import Q, Min, F
from django.contrib.staticfiles import finders
from django.forms import formset_factory
from fpdf import FPDF
from django.conf import settings
from django.contrib.staticfiles import finders
import random
import tempfile
import base64
import json
# self
from django.db import models
from .models import Diploma, CustomUser, UserProfile, Course, Lesson, Activity, Question, Option, Grade, ActivityQuestion
from .forms import CustomUserCreationForm, UserProfileForm, CertificationForm, DiplomaForm, CourseForm, LessonForm, ActivityForm, MCQForm, QuestionBankForm

# Create your views here.


def home(request):
    query = request.GET.get('q', '')  # Retrieve the search query with 'q' as the parameter name

    if query:
        # Filter courses based on the query; adjust fields according to your model
        courses = Course.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)  # Assuming you have a 'description' field
        )
    else:
        courses = Course.objects.all()  # Query all courses if there's no search query

    return render(request, 'edu_core/home.html', {'courses': courses, 'query': query})


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')  # Redirect to login page upon successful registration
    template_name = 'edu_core/signup.html'


@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'edu_core/profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    certifications = profile.certifications.all()
    max_certifications = 5  # Maximum number of certifications allowed

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        certification_form = CertificationForm(request.POST, request.FILES)

        if 'profile_form' in request.POST and profile_form.is_valid():
            profile_form.save()
            return redirect('profile')
        elif 'certification_form' in request.POST:
            if certification_form.is_valid():
                # Check if the limit of certifications is reached
                if certifications.count() >= max_certifications:
                    # Find the oldest certification and delete it
                    oldest_certification = certifications.aggregate(Min('id'))['id__min']
                    certification_to_delete = Certification.objects.get(id=oldest_certification)
                    certification_to_delete.delete()
                
                # Save the new certification
                new_certification = certification_form.save(commit=False)
                new_certification.user_profile = profile
                new_certification.save()
                return redirect('edit_profile')

    else:
        profile_form = UserProfileForm(instance=profile)
        certification_form = CertificationForm()

    return render(request, 'edu_core/edit_profile.html', {
        'profile_form': profile_form,
        'certification_form': certification_form,
        'certifications': certifications
    })


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def diploma_search(request):
    query = request.GET.get("query", "")
    if query:
        diplomas = Diploma.objects.filter(
            Q(verification_key__icontains=query) | 
            Q(student_name__icontains=query)
        ).distinct()
    else:
        diplomas = Diploma.objects.none()  # Return an empty query if no query is provided

    return render(request, 'edu_core/diploma_search.html', {'diplomas': diplomas})


def view_diploma_online(request, pk):
    diploma = get_object_or_404(Diploma, pk=pk)
    return render(request, 'edu_core/diploma_view.html', {'diploma': diploma})


def download_diploma_pdf(request, verification_key):
    # Retrieve the diploma details
    diploma = get_object_or_404(Diploma, verification_key=verification_key)

    # Find image paths
    logo_path = finders.find('edu_core/images/Education Villa logo 2.jpg')
    signature_path = finders.find('edu_core/images/evsignature.jpg')
    evx_logo_path = finders.find('edu_core/images/EVX logo 1.jpg')

    # Create an instance of FPDF and add a page
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    # Set a border around the page
    pdf.set_line_width(0.5)
    pdf.rect(10, 10, 277, 190)

    # Add the main title "Certificate"
    pdf.set_font('Arial', 'B', 30)
    pdf.set_xy(0, 40)
    pdf.cell(0, 20, 'Certificate', ln=True, align='C')

    # Add subtitle "to certify that"
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, 'to certify that', ln=True, align='C')

    # Add the student name
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 15, diploma.student_name, ln=True, align='C')

    # Add the course completion statement
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, 'received passing grades and successfully completed', ln=True, align='C')

    # Add the course name
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, diploma.course_name, ln=True, align='C')

    # Add "a course offered by Education Villa"
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, 'a course offered by Education Villa', ln=True, align='C')

    # Add issued date and verification key at the bottom
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Issued by: {diploma.issued_by.get_full_name()} on {diploma.issue_date}", ln=True, align='C')
    pdf.cell(0, 10, f"Verification Key: {diploma.verification_key}", ln=True, align='C')

    # Add images: Left side for the logo, right side for the EVX logo
    if logo_path:
        pdf.image(logo_path, x=20, y=30, w=40)  # Adjust size and position for left-side logo
    if evx_logo_path:
        pdf.image(evx_logo_path, x=240, y=150, w=30)  # Adjust size and position for right-side logo
    if signature_path:
        pdf.image(signature_path, x=20, y=160, w=40)  # Adjust position for the signature

    # Output PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diploma_{verification_key}.pdf"'
    response.write(pdf.output(dest='S').encode('latin1'))

    return response


@login_required
def create_diploma(request):
    if request.method == 'POST':
        form = DiplomaForm(request.POST)
        if form.is_valid():
            diploma = form.save(commit=False)
            diploma.issued_by = request.user  # Automatically set the issuing user
            diploma.save()
            return redirect('view_diploma', pk=diploma.pk)
    else:
        form = DiplomaForm()
    return render(request, 'edu_core/diploma_create.html', {'form': form})


@login_required
def create_course(request):
    # Check if the user's profile exists and has been edited
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.bio or not user_profile.profile_picture:
            return redirect('edit_profile')
    except UserProfile.DoesNotExist:
        return redirect('edit_profile')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'edu_core/course_create.html', {'form': form})


def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, 'edu_core/course.html', {'course': course})


@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, id=pk)

    # Allow the author or a superuser to delete the course
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    course.delete()
    return redirect('home')


@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Allow the author or a superuser to edit the course
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'edu_core/course_edit.html', {'form': form, 'course': course})


@login_required
def lesson_add(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Allow the author or a superuser to add lessons
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_id=course_id)
    else:
        form = LessonForm()
    return render(request, 'edu_core/lesson_add.html', {'form': form, 'course_id': course_id})


def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'edu_core/lesson_view.html', {'lesson': lesson})


@login_required
def activity_add(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Allow the course author or a superuser to add activities
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
    return render(request, 'edu_core/activity_add.html', {'form': form, 'lesson': lesson})


@login_required
def delete_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Ensure only the course author or a superuser can delete the activity
    if request.user == activity.lesson.course.author or request.user.is_superuser:
        activity.delete()
        messages.success(request, 'The activity has been successfully deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this activity.')

    return redirect('lesson_view', lesson_id=activity.lesson.id)


@login_required
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    current_date = timezone.now().date()  # Get the current date
    
    # Check if the activity is available based on start_date and end_date
    if (activity.start_date and current_date < activity.start_date) or (activity.end_date and current_date > activity.end_date):
        messages.error(request, 'This activity is not available at this time.')
        return redirect('lesson_view', lesson_id=activity.lesson.id)

    activity_questions = ActivityQuestion.objects.filter(activity=activity).select_related('question').order_by('order')
    total_pages = activity_questions.aggregate(models.Max('page_number'))['page_number__max'] or 1
    page = int(request.GET.get('page', 1))

    # Filter questions by page number, excluding separators
    questions_on_page = activity_questions.filter(page_number=page).exclude(question__isnull=True)
    
    grade_history = Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at')

    if request.method == 'POST' and 'retry' not in request.POST:
        # Process the submitted answers
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

        # Store the grade
        Grade.objects.create(
            student=request.user,
            activity=activity,
            score=percentage_score
        )

        return render(request, 'edu_core/activity_views/activity_view.html', {
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
        # Prepare the questions and randomize options if necessary
        for aq in questions_on_page:
            question = aq.question
            options = list(question.options.all())
            if question.randomize_options:
                random.shuffle(options)  # Shuffle the options
            question.shuffled_options = options  # Attach shuffled options to question

        return render(request, 'edu_core/activity_views/activity_view.html', {
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
    
    insert_after_order = int(request.GET.get('insert_after', 0))  # Capture the 'insert_after' value from the GET parameters
    
    if request.method == 'POST':
        form = MCQForm(request.POST)
        if form.is_valid():
            # Create the question
            question = Question.objects.create(
                text=form.cleaned_data['question_text'],
                question_type=Question.MULTIPLE_CHOICE,
                correct_answer=form.cleaned_data['correct_answer'],
                randomize_options=form.cleaned_data.get('randomize_options', False),
                key_name=form.cleaned_data.get('key_name', ''),
                course=course  # Automatically relate the course
            )

            # Save the question to the bank if needed
            if form.cleaned_data.get('add_to_bank', True):
                question.in_bank = True
                question.save()

            with transaction.atomic():
                # Temporarily set the order of existing questions to a very high number
                ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + 1000)

                # Determine the page number for the new question
                previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
                if previous_question:
                    page_number = previous_question.page_number
                else:
                    # If no previous question, set page_number to 1
                    page_number = 1

                # Insert the new question after the selected question
                new_activity_question = ActivityQuestion.objects.create(
                    activity=activity,
                    question=question,
                    order=insert_after_order + 1,
                    page_number=page_number
                )

                # Reassign the correct order to all questions
                questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
                for idx, aq in enumerate(questions_to_reorder):
                    aq.order = idx + 1
                    aq.save()

            # Create options for the question
            for option_number in range(1, 5):
                option_text = form.cleaned_data.get(f'option_{option_number}')
                if option_text:
                    Option.objects.create(
                        question=question,
                        text=option_text,
                        is_correct=(f'option_{option_number}' == form.cleaned_data['correct_answer'])
                    )

            return redirect('activity_view', activity_id=activity.id)
    else:
        form = MCQForm()
    
    return render(request, 'edu_core/activity_forms/mcq_creator.html', {'form': form, 'activity': activity})


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

    return render(request, 'edu_core/activity_forms/mcq_creator.html', {'form': form, 'course': course})


@login_required
def question_type_selection(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    return render(request, 'edu_core/activity_views/question_type_selection.html', {'activity': activity})


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
            question.is_in_bank = True
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
    return render(request, 'edu_core/question_bank/edit_question_in_bank.html', {'form': form, 'question': question})


@login_required
def question_type_selection_for_bank(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'edu_core/activity_views/question_type_selection.html', {'course': course})


@login_required
def select_from_bank(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    course = activity.lesson.course
    query = request.GET.get('q', '')
    insert_after_order = int(request.GET.get('insert_after', 0))  # Capture the 'insert_after' value from the GET parameters

    # Get all questions in the bank for this course
    questions = Question.objects.filter(course=course, in_bank=True)

    # Apply search filter if a query is provided
    if query:
        questions = questions.filter(
            Q(key_name__icontains=query) | Q(text__icontains=query)
        )

    if request.method == 'POST':
        selected_question_ids = request.POST.getlist('selected_questions')

        with transaction.atomic():
            # Shift the order of existing questions to make room for the new questions
            ActivityQuestion.objects.filter(activity=activity, order__gt=insert_after_order).update(order=F('order') + len(selected_question_ids) + 1000)

            # Determine the page number to use for the new questions
            previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
            new_page_number = previous_question.page_number if previous_question else 1

            # Insert the new questions after the selected question
            for i, question_id in enumerate(selected_question_ids):
                question = get_object_or_404(Question, id=question_id)
                ActivityQuestion.objects.create(
                    activity=activity,
                    question=question,
                    order=insert_after_order + i + 1,  # Insert after the selected question
                    page_number=new_page_number  # Use the determined page number
                )

            # Reassign the correct order to all questions
            questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
            for idx, aq in enumerate(questions_to_reorder):
                aq.order = idx + 1
                aq.save()

        return redirect('activity_view', activity_id=activity.id)

    return render(request, 'edu_core/activity_views/select_from_bank.html', {
        'activity': activity,
        'questions': questions,
        'query': query,
    })


@login_required
@csrf_exempt
def save_question_order(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        data = json.loads(request.body)
        order = data.get('order', [])

        # Log received order data for debugging
        print("Received Order Data:", order)

        with transaction.atomic():
            for item in order:
                question_id = item.get('id')
                question_order = item.get('order')
                page_number = item.get('page_number')

                # Log each update for debugging
                print(f"Updating Question ID: {question_id}, Order: {question_order}, Page Number: {page_number}")

                # Update only the order and page_number explicitly provided by the frontend
                ActivityQuestion.objects.filter(activity=activity, question_id=question_id).update(
                    order=question_order,
                    page_number=page_number
                )

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)


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

    # Load the activity's questions in order
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')

    return render(request, 'edu_core/activity_views/activity_edit.html', {
        'activity': activity,
        'form': form,
        'activity_questions': activity_questions,
    })


def correct_question_order(activity):
    """ Ensures that all questions have a unique, sequential order """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    expected_order = 1

    with transaction.atomic():
        for aq in activity_questions:
            if aq.order != expected_order:
                aq.order = expected_order
                aq.save()
            expected_order += 1


def update_page_numbers(activity):
    """ Updates page numbers based on current order, considering separators """
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')
    current_page_number = 1

    for aq in activity_questions:
        if aq.is_separator:
            current_page_number += 1
        aq.page_number = current_page_number
        aq.save()


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
            # Remove the question from the activity
            question_to_remove = ActivityQuestion.objects.get(id=remove_question_id, activity=activity)
            question_to_remove.delete()

            # Adjust the order of remaining questions
            questions_to_reorder = ActivityQuestion.objects.filter(activity=activity).order_by('order')
            for idx, aq in enumerate(questions_to_reorder):
                aq.order = idx + 1
                aq.save()

            # Update page numbers
            update_page_numbers(activity)

    elif remove_page_number:
        with transaction.atomic():
            # Remove the page separator
            page_to_remove = ActivityQuestion.objects.get(activity=activity, is_separator=True, page_number=remove_page_number)
            page_to_remove.delete()

            # Adjust the page numbers of the following questions
            following_questions = ActivityQuestion.objects.filter(activity=activity, page_number__gt=remove_page_number).order_by('order')
            for aq in following_questions:
                aq.page_number -= 1
                aq.save()

            # Reorder questions
            correct_question_order(activity)

            # Update page numbers
            update_page_numbers(activity)

    correct_question_order(activity)

    return redirect('edit_activity', activity_id=activity.id)


@require_POST
def add_page(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        # Determine where to insert the new page
        if insert_after_order == 0:
            new_order = 1
        else:
            new_order = insert_after_order + 1

        # Increment the order of all questions after the new page one by one
        questions_to_shift = ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).order_by('-order')
        for question in questions_to_shift:
            question.order += 1
            question.save()

        # Determine the new page number
        previous_question = ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first()
        if previous_question:
            page_number = previous_question.page_number + 1
        else:
            page_number = 1

        # Create the new page separator with the correct order and page number
        new_separator = ActivityQuestion.objects.create(
            activity=activity,
            order=new_order,
            page_number=page_number,
            is_separator=True
        )

        # Increment page numbers for all subsequent questions
        for question in ActivityQuestion.objects.filter(activity=activity, order__gt=new_order).order_by('order'):
            question.page_number += 1
            question.save()

    return redirect('edit_activity', activity_id=activity.id)


@require_POST
def add_question_to_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    question_id = request.POST.get('question_id')  # Assuming you're selecting a question from the bank
    insert_after_order = int(request.POST.get('insert_after', 0))

    with transaction.atomic():
        # Determine where to insert the new question
        if insert_after_order == 0:
            new_order = 1
        else:
            new_order = insert_after_order + 1

        # Increment the order of all questions after the new question one by one
        questions_to_shift = ActivityQuestion.objects.filter(activity=activity, order__gte=new_order).order_by('-order')
        for question in questions_to_shift:
            question.order += 1
            question.save()

        # Add the new question at the correct position
        new_activity_question = ActivityQuestion.objects.create(
            activity=activity,
            question_id=question_id,
            order=new_order,
            page_number=ActivityQuestion.objects.filter(activity=activity, order=insert_after_order).first().page_number,
            is_separator=False
        )

        # Adjust page numbers if needed (if the new question affects pagination)
        update_page_numbers(activity)

    return redirect('edit_activity', activity_id=activity.id)


@login_required
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Ensure only the course author or a superuser can delete the lesson
    if request.user == course.author or request.user.is_superuser:
        lesson.delete()
        messages.success(request, 'The lesson has been successfully deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this lesson.')

    return redirect('course_detail', course_id=course.id)
