# Portfolio\Education_Villa\edu_core\views\lesson_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Lesson, Course
from ..forms import LessonForm

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
    return render(request, 'edu_core/lesson/lesson_add.html', {'form': form, 'course_id': course_id})


def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'edu_core/lesson/lesson_view.html', {'lesson': lesson})


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
