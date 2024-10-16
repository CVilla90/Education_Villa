# Portfolio\Education_Villa\edu_core\decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Registration

def course_access_check(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        if request.user.is_authenticated and course_id:
            registration = Registration.objects.filter(student=request.user, course_id=course_id).first()
            if registration and registration.is_banned:
                messages.error(request, "You are banned from this course.")
                return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
