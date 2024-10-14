# Portfolio\Education_Villa\edu_core\views\activity_dashboard_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from ..models import Activity, ActivityAttempt, Grade

@login_required
def activity_dashboard(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)

    # Ensure the current user is either the author of the course or a superuser
    if request.user != activity.lesson.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to access this dashboard.")

    # Get all attempts for the given activity and their associated grades
    activity_attempts = []
    attempts = ActivityAttempt.objects.filter(activity=activity)

    for attempt in attempts:
        grade = Grade.objects.filter(activity=activity, student=attempt.user).first()
        activity_attempts.append({
            'attempt': attempt,
            'grade': grade.score if grade else 'N/A'
        })

    return render(request, 'edu_core/activity/activity_dashboard.html', {
        'activity': activity,
        'activity_attempts': activity_attempts
    })

@login_required
def delete_attempt(request, attempt_id):
    attempt = get_object_or_404(ActivityAttempt, id=attempt_id)
    activity = attempt.activity

    # Ensure only the course author or superuser can delete the attempt
    if request.user != activity.lesson.course.author and not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to delete this attempt.")

    # Delete any associated grades for this attempt
    Grade.objects.filter(activity=activity, student=attempt.user).delete()

    # Delete the attempt
    attempt.delete()

    return redirect('activity_dashboard', activity_id=activity.id)
