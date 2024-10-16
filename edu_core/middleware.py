# Portfolio\Education_Villa\edu_core\middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import Registration

class BanCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Make sure `resolver_match` is not None
            resolver_match = request.resolver_match
            if resolver_match:
                # Get course_id if present
                course_id = resolver_match.kwargs.get('course_id')
                if course_id:
                    # Check if the user is banned for this course
                    registration = Registration.objects.filter(student=request.user, course_id=course_id).first()
                    if registration and registration.is_banned:
                        messages.error(request, "You have been banned from accessing this course.")
                        return redirect('home')

        # Proceed with the response as usual
        response = self.get_response(request)
        return response
