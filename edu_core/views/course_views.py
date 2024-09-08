# Portfolio\Education_Villa\edu_core\views\course_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Course, UserProfile
from ..forms import CourseForm

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
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'edu_core/course/course_create.html', {'form': form})


def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, 'edu_core/course/course.html', {'course': course})


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
    return render(request, 'edu_core/course/course_edit.html', {'form': form, 'course': course})
