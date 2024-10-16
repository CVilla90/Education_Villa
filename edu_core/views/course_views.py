# Portfolio\Education_Villa\edu_core\views\course_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from ..models import Course, UserProfile, Registration, Grade, Lesson
from ..forms import CourseForm
from ..decorators import course_access_check

@login_required
def create_course(request):
    # Ensure the UserProfile exists
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Check if the profile has required fields filled
    if not profile.bio or not profile.profile_picture:
        messages.info(request, 'Please complete your profile to create a course.')
        return redirect('edit_profile')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            
            # Register the author as the professor of the course
            Registration.objects.create(student=request.user, course=course, role=Registration.PROFESSOR)

            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'edu_core/course/course_create.html', {'form': form})


@login_required
@course_access_check
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user if request.user.is_authenticated else None
    registered = course.registrations.filter(student=user).exists() if user else False

    # Restrict student access if the course is paused
    if course.paused and user and user != course.author and not user.is_superuser:
        context = {'course': course, 'paused': True}
        return render(request, 'edu_core/course/course_paused.html', context)

    context = {
        'course': course,
        'registered': registered,
        'is_author_or_superuser': user == course.author or (user and user.is_superuser),
    }

    return render(request, 'edu_core/course/course.html', context)


@login_required
def register_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    if request.method == 'POST':
        if 'register' in request.POST:
            Registration.objects.get_or_create(student=user, course=course, defaults={'role': Registration.STUDENT})
            messages.success(request, f"You have successfully registered for {course.name}.")
        elif 'unregister' in request.POST:
            registration = Registration.objects.filter(student=user, course=course).first()
            if registration:
                registration.delete()
                messages.success(request, f"You have successfully unregistered from {course.name}.")
    
    return redirect('course_detail', course_id=course.id)


@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, id=pk)

    # Allow the author or a superuser to delete the course
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    course.delete()
    messages.success(request, f"The course '{course.name}' has been successfully deleted.")
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
            messages.success(request, f"The course '{course.name}' has been successfully updated.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'edu_core/course/course_edit.html', {'form': form, 'course': course})


@login_required
def course_dashboard(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Ensure the current user is either the author of the course or a superuser
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    # Get all students registered for the course
    registered_students = Registration.objects.filter(course=course).select_related('student')

    # Gather lesson and student grade data
    lessons = course.lessons.all()
    summary_data = []
    for student_registration in registered_students:
        student = student_registration.student
        student_activities = []

        # Iterate through each lesson
        for lesson in lessons:
            lesson_activities = lesson.activities.all()

            # Find the highest grade for the student in each lesson
            highest_grade = Grade.objects.filter(activity__in=lesson_activities, student=student).aggregate(Max('score'))['score__max']
            student_activities.append({
                'lesson': lesson,
                'highest_grade': highest_grade
            })

        # Calculate the average score across the course for the student (based on highest grades per activity)
        highest_grades = Grade.objects.filter(activity__lesson__course=course, student=student).values('activity').annotate(max_score=Max('score')).values_list('max_score', flat=True)
        average_score = sum(highest_grades) / len(highest_grades) if highest_grades else None

        summary_data.append({
            'student': student,
            'student_activities': student_activities,
            'average_score': average_score
        })

    # Calculate class averages for each lesson
    class_averages = []
    for lesson in lessons:
        lesson_activities = lesson.activities.all()

        # Calculate class average based on the highest score per student in each activity
        highest_grades = Grade.objects.filter(activity__in=lesson_activities).values('student').annotate(max_score=Max('score')).values_list('max_score', flat=True)
        lesson_average = sum(highest_grades) / len(highest_grades) if highest_grades else None
        class_averages.append({
            'lesson': lesson,
            'class_average': lesson_average
        })

    context = {
        'course': course,
        'registered_students': registered_students,
        'summary_data': summary_data,
        'class_averages': class_averages,
    }

    return render(request, 'edu_core/course/course_dashboard.html', context)


@login_required
@csrf_exempt
def toggle_pause_course(request, course_id):
    if request.method == 'POST':
        try:
            course = get_object_or_404(Course, id=course_id)

            # Only allow the author or a superuser to pause/resume the course
            if request.user != course.author and not request.user.is_superuser:
                return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

            # Get the pause status from request body
            data = json.loads(request.body)
            course.paused = data['pause']
            course.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
@csrf_exempt
def toggle_ban(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    # Only allow the course author or superuser to toggle ban status
    if request.user != registration.course.author and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied.'})

    if request.method == 'POST':
        data = json.loads(request.body)
        print(f"Data received: {data}")  # Print statement to see data received
        registration.is_banned = data.get('is_banned', False)
        registration.save()
        print(f"Registration status updated: {registration.is_banned}")  # Print to confirm if saved
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request.'})



@login_required
@csrf_exempt
def remove_student(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    # Only allow the course author or superuser to remove a student
    if request.user != registration.course.author and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied.'})

    if request.method == 'POST':
        registration.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request.'})