# Portfolio\Education_Villa\edu_core\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views import generic
from django.db.models import Q, Min
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS
import tempfile
import base64
import json
# self
from .models import Diploma, CustomUser, UserProfile, Course, Lesson, Activity, Question
from .forms import CustomUserCreationForm, UserProfileForm, CertificationForm, DiplomaForm, CourseForm, LessonForm, ActivityForm, MCQForm

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


def create_course(request):
    # Check if the user's profile exists and has been edited
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        if not user_profile.bio or not user_profile.profile_picture:
            # Redirect to the profile edit page if bio or profile picture is missing
            return redirect('edit_profile')
    except UserProfile.DoesNotExist:
        # Redirect to create a profile if the profile does not exist
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
def delete_course(request, pk):  # Changed from course_id to pk
    course = get_object_or_404(Course, id=pk)  # Use pk to fetch the course
    if request.user == course.author or request.user.is_superuser:
        course.delete()
        return redirect('home')  # Use 'home' directly if you've imported the redirect function
    else:
        return redirect('home')


@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, author=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'edu_core/course_edit.html', {'form': form, 'course': course})


def lesson_add(request, course_id):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course_id = course_id
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
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.lesson = lesson
            activity.save()
            # Redirect back to the lesson view
            return redirect('lesson_view', lesson_id=lesson.id)
    else:
        form = ActivityForm()
    return render(request, 'edu_core/activity_add.html', {'form': form, 'lesson': lesson})


@login_required
def activity_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    questions = activity.questions.all()  # Assuming a related_name='questions' in your Question model
    
    if request.method == 'POST':
        # Example for adding a MCQ. You might have different forms for different question types
        mcq_form = MCQForm(request.POST)
        if mcq_form.is_valid():
            question = mcq_form.save(commit=False)
            question.activity = activity
            question.save()
            # Redirect back to refresh the form and list updated questions
            return redirect('activity_view', activity_id=activity.id)
    else:
        mcq_form = MCQForm()

    return render(request, 'edu_core/activity_views/activity_view.html', {
        'activity': activity,
        'questions': questions,
        'mcq_form': mcq_form  # Pass the MCQ form to the template
    })


@login_required
def add_mcq(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if request.method == 'POST':
        form = MCQForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('activity_detail', activity_id=activity.id)
    else:
        form = MCQForm()
    return render(request, 'edu_core/add_mcq.html', {'form': form, 'activity': activity})


@login_required
def mcq_view(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    structured_content = activity.structured_content

    if request.method == 'POST':
        selected_option = request.POST.get('answer')
        is_correct = selected_option == structured_content['correct_answer']

        # Provide instant feedback on the same page or redirect as needed
        return JsonResponse({'correct': is_correct, 'selected_option': selected_option, 'correct_answer': structured_content['correct_answer']})

    return render(request, 'edu_core/activity_views/mcq_view.html', {
        'activity': activity,
        'structured_content': structured_content,
    })    
