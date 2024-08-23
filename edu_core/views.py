# Portfolio\Education_Villa\edu_core\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views import generic
from django.db.models import Q, Min
from django.contrib.staticfiles import finders
from django.forms import formset_factory
from weasyprint import HTML, CSS
import random
import tempfile
import base64
import json
# self
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
    diploma = get_object_or_404(Diploma, verification_key=verification_key)

    # Get the absolute file system paths to the images
    logo_path = finders.find('edu_core/images/Education Villa logo 2.jpg')
    signature_path = finders.find('edu_core/images/evsignature.jpg')
    evx_logo_path = finders.find('edu_core/images/EVX logo 1.jpg')

    # Encode the images using the absolute paths
    logo_image_base64 = get_base64_encoded_image(logo_path)
    signature_image_base64 = get_base64_encoded_image(signature_path)
    evx_logo_image_base64 = get_base64_encoded_image(evx_logo_path)

    # Get the absolute file system path to the CSS
    css_path = finders.find('edu_core/css/diploma_pdf.css')

    # Pass the encoded images to the template context
    context = {
        'diploma': diploma,
        'logo_image_base64': logo_image_base64,
        'signature_image_base64': signature_image_base64,
        'evx_logo_image_base64': evx_logo_image_base64,
    }

    # Render the HTML template with the provided context
    html_string = render_to_string('edu_core/diploma_pdf.html', context)

    # Create the HTML and CSS objects for WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    css = CSS(filename=css_path)

    # Generate the PDF
    pdf = html.write_pdf(stylesheets=[css])

    # Create the HTTP response with the PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diploma_{verification_key}.pdf"'
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
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    activity_questions = ActivityQuestion.objects.filter(activity=activity).select_related('question').order_by('order')
    grade_history = Grade.objects.filter(student=request.user, activity=activity).order_by('-created_at')

    if request.method == 'POST' and 'retry' not in request.POST:
        # Process the submitted answers
        score = 0
        total_questions = activity_questions.count()
        results = {}

        for aq in activity_questions:
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
        })

    else:
        # Prepare the questions and randomize options if necessary
        for aq in activity_questions:
            question = aq.question
            options = list(question.options.all())
            if question.randomize_options:
                random.shuffle(options)  # Shuffle the options
            question.shuffled_options = options  # Attach shuffled options to question

        return render(request, 'edu_core/activity_views/activity_view.html', {
            'activity': activity,
            'activity_questions': activity_questions,
            'grade_history': grade_history,
        })


@login_required
def add_mcq(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    lesson = activity.lesson
    course = lesson.course
    
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

            # Add the question to the activity with the correct order
            last_order = ActivityQuestion.objects.filter(activity=activity).count()
            ActivityQuestion.objects.create(
                activity=activity,
                question=question,
                order=last_order + 1
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
    
    # Get all questions in the bank for this course
    questions = Question.objects.filter(course=course, in_bank=True)

    # Apply search filter if a query is provided
    if query:
        questions = questions.filter(
            Q(key_name__icontains=query) | Q(text__icontains=query)
        )
    
    if request.method == 'POST':
        selected_question_ids = request.POST.getlist('selected_questions')
        last_order = ActivityQuestion.objects.filter(activity=activity).count()

        for i, question_id in enumerate(selected_question_ids, start=1):
            question = get_object_or_404(Question, id=question_id)
            # Create a new ActivityQuestion instance
            ActivityQuestion.objects.create(
                activity=activity,
                question=question,
                order=last_order + i  # Continue the order incrementally
            )

        return redirect('activity_view', activity_id=activity_id)

    return render(request, 'edu_core/activity_views/select_from_bank.html', {
        'activity': activity,
        'questions': questions,
        'query': query,
    })


@login_required
@csrf_exempt  # Use this to handle the AJAX POST request
def save_question_order(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        data = json.loads(request.body)  # Parse the JSON data from the request
        order = data.get('order', [])

        for item in order:
            question_id = item.get('id')
            question_order = item.get('order')

            # Update the order of the question in the activity
            ActivityQuestion.objects.filter(activity=activity, question_id=question_id).update(order=question_order)

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)
