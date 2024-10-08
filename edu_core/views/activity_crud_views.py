# Portfolio\Education_Villa\edu_core\views\activity_crud_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Activity, ActivityQuestion, Lesson
from ..forms import ActivityForm


@login_required
def activity_add(request, lesson_id):
    """
    Add a new activity to a lesson.
    
    Args:
        request: The HTTP request object.
        lesson_id: The ID of the lesson to which the activity is being added.
    
    Returns:
        HTTP Response rendering the activity add form or redirecting to the lesson view.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.course

    # Ensure the current user is either the author of the course or a superuser
    if request.user != course.author and not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            # Save the activity with the current lesson and other details
            activity = form.save(commit=False)
            activity.lesson = lesson
            
            # Handle unlimited_attempts separately
            unlimited_attempts = request.POST.get('unlimited_attempts', 'off') == 'on'
            if unlimited_attempts:
                activity.unlimited_attempts = True
                activity.max_attempts = None  # Set to None when unlimited attempts are allowed
            else:
                activity.unlimited_attempts = False
                max_attempts = request.POST.get('max_attempts')
                # Set max_attempts only if the user provided a value, otherwise use default of 1
                activity.max_attempts = int(max_attempts) if max_attempts else 1

            activity.save()
            return redirect('lesson_view', lesson_id=lesson.id)
    else:
        form = ActivityForm()
    
    # Render the activity add form
    return render(request, 'edu_core/activity/activity_add.html', {
        'form': form,
        'lesson': lesson,
    })


@login_required
def delete_activity(request, activity_id):
    """
    Delete an existing activity.
    
    Args:
        request: The HTTP request object.
        activity_id: The ID of the activity to be deleted.
    
    Returns:
        HTTP Response redirecting to the lesson view.
    """
    activity = get_object_or_404(Activity, id=activity_id)

    # Ensure the current user is either the author of the course or a superuser
    if request.user == activity.lesson.course.author or request.user.is_superuser:
        activity.delete()
        messages.success(request, 'The activity has been successfully deleted.')
    else:
        messages.error(request, 'You do not have permission to delete this activity.')

    return redirect('lesson_view', lesson_id=activity.lesson.id)


@login_required
def edit_activity(request, activity_id):
    """
    Edit an existing activity, including reordering questions.
    
    Args:
        request: The HTTP request object.
        activity_id: The ID of the activity to be edited.
    
    Returns:
        HTTP Response rendering the activity edit form or redirecting to the lesson view.
    """
    activity = get_object_or_404(Activity, id=activity_id)

    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            # Save the updated activity
            updated_activity = form.save(commit=False)
            # Handle unlimited_attempts separately
            unlimited_attempts = request.POST.get('unlimited_attempts', 'off') == 'on'
            if unlimited_attempts:
                updated_activity.unlimited_attempts = True
                updated_activity.max_attempts = None  # Set to None when unlimited attempts are allowed
            else:
                updated_activity.unlimited_attempts = False
                max_attempts = request.POST.get('max_attempts')
                # Set max_attempts only if the user provided a value, otherwise use default of 1
                updated_activity.max_attempts = int(max_attempts) if max_attempts else 1
            updated_activity.save()
            return redirect('lesson_view', lesson_id=activity.lesson.id)
    else:
        form = ActivityForm(instance=activity)

    # Fetch all activity questions including content blocks to be rendered in the template
    activity_questions = ActivityQuestion.objects.filter(activity=activity).order_by('order')

    return render(request, 'edu_core/activity/activity_edit.html', {
        'activity': activity,
        'form': form,
        'activity_questions': activity_questions,
    })
