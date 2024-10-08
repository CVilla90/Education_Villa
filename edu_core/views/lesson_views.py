# Portfolio\Education_Villa\edu_core\views\lesson_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from ..models import Lesson, Course
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

        activities_with_attempts.append({
            'activity': activity,
            'user_attempts': user_attempts,
            'max_attempts': activity.max_attempts,
            'unlimited_attempts': activity.unlimited_attempts,
            'attempts_left': attempts_left
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
