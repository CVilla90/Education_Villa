# Portfolio\Education_Villa\edu_core\urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Landing
    path('', views.home, name='home'),

    # Authentication
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # User Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Diploma Management
    path('diploma/search/', views.diploma_search, name='diploma_search'),
    path('diploma/view/<int:pk>/', views.view_diploma_online, name='view_diploma'),
    path('diploma/download/<str:verification_key>/', views.download_diploma_pdf, name='download_diploma_pdf'),
    path('diploma/create/', views.create_diploma, name='create_diploma'),

    # Course Management
    path('create-course/', views.create_course, name='create_course'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/delete/<int:pk>/', views.delete_course, name='delete_course'),
    path('courses/edit/<int:course_id>/', views.edit_course, name='edit_course'),

    # Lesson Management
    path('courses/<int:course_id>/lesson_add/', views.lesson_add, name='lesson_add'),    
    path('lessons/<int:lesson_id>/', views.lesson_view, name='lesson_view'),

    # Activity Management
    path('lessons/<int:lesson_id>/activity_add/', views.activity_add, name='activity_add'),
    path('activities/<int:activity_id>/', views.activity_view, name='activity_view'),
    path('activities/<int:activity_id>/mcq/', views.mcq_view, name='mcq_view'),  # Adjusted for direct MCQ view
    
    # Additional paths for other activity types as needed

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
