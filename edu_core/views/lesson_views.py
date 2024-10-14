# Portfolio\Education_Villa\edu_core\views\lesson_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from ..models import CustomUser, Lesson, Course, Grade
from ..forms import LessonForm
from django.http import HttpResponseForbidden


@login_required
def lesson_add(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Allow only the author or a superuser to add lessons
    if request.user != course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to add lessons to this course.")

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_id=course_id)
    else:
        form = LessonForm()
    return render(request, 'edu_core/lesson/lesson_add.html', {'form': form, 'course_id': course_id})


@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Determine if the user is the author or a superuser
    is_author_or_superuser = request.user == lesson.course.author or request.user.is_superuser

    activities_with_attempts = []
    for activity in lesson.activities.all():
        user_attempts = activity.attempts.filter(user=request.user).count()

        # Calculate the number of attempts left
        if activity.unlimited_attempts:
            attempts_left = "No limit"
        else:
            attempts_left = max(activity.max_attempts - user_attempts, 0)
            if attempts_left == 0:
                attempts_left = "No attempts left"

        # Get the highest grade for this activity if any
        highest_grade = Grade.objects.filter(activity=activity, student=request.user).aggregate(Max('score'))['score__max']


        activities_with_attempts.append({
            'activity': activity,
            'user_attempts': user_attempts,
            'max_attempts': activity.max_attempts,
            'unlimited_attempts': activity.unlimited_attempts,
            'attempts_left': attempts_left,
            'highest_grade': highest_grade
        })

    return render(request, 'edu_core/lesson/lesson_view.html', {
        'lesson': lesson,
        'activities_with_attempts': activities_with_attempts,
        'is_author_or_superuser': is_author_or_superuser
    })


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


@login_required
def lesson_dashboard(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Ensure only the course author or superuser can view the dashboard
    if request.user != lesson.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this dashboard.")

    summary_data = []
    students = CustomUser.objects.filter(course_registrations__course=lesson.course)
    for student in students:
        student_activities = []
        for activity in lesson.activities.all():
            highest_grade = Grade.objects.filter(activity=activity, student=student).aggregate(Max('score'))['score__max']
            student_activities.append({
                'activity': activity,
                'highest_grade': highest_grade
            })

        # Calculate average score based on the highest grade for each activity
        highest_grades = [grade['highest_grade'] for grade in student_activities if grade['highest_grade'] is not None]
        average_score = sum(highest_grades) / len(highest_grades) if highest_grades else None

        summary_data.append({
            'student': student,
            'student_activities': student_activities,
            'average_score': average_score
        })

    # Calculate class averages for each activity based on the highest grade of each student
    class_averages = []
    for activity in lesson.activities.all():
        highest_grades = Grade.objects.filter(activity=activity).values('student').annotate(max_score=Max('score')).values_list('max_score', flat=True)
        class_average = sum(highest_grades) / len(highest_grades) if highest_grades else None
        class_averages.append({
            'activity': activity,
            'class_average': class_average
        })

    return render(request, 'edu_core/lesson/lesson_dashboard.html', {
        'lesson': lesson,
        'summary_data': summary_data,
        'class_averages': class_averages
    })