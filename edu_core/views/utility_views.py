# Portfolio\Education_Villa\edu_core\views\utility_views.py

from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
import base64, os
from ..models import Course

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

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        course_list = [{
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'image_url': course.image.url if course.image else '',
        } for course in courses]
        return JsonResponse({'courses': course_list})
    
    return render(request, 'edu_core/home.html', {'courses': courses, 'query': query})

def get_base64_encoded_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return None
