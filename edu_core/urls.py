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
    path('lessons/<int:lesson_id>/delete/', views.delete_lesson, name='delete_lesson'),

    # Activity Management
    path('lessons/<int:lesson_id>/activity_add/', views.activity_add, name='activity_add'),
    path('activities/<int:activity_id>/delete/', views.delete_activity, name='delete_activity'),
    path('activities/<int:activity_id>/', views.activity_view, name='activity_view'),
    path('activities/<int:activity_id>/add_mcq/', views.add_mcq, name='add_mcq'),
    path('activities/<int:activity_id>/question_type_selection/', views.question_type_selection, name='question_type_selection'),
    path('activities/<int:activity_id>/select_from_bank/', views.select_from_bank, name='select_from_bank'),
    path('activities/<int:activity_id>/edit/', views.edit_activity, name='edit_activity'),
    path('activities/<int:activity_id>/reorder_questions/', views.reorder_questions, name='reorder_questions'),
    path('activities/<int:activity_id>/add_page/', views.add_page, name='add_page'),  # Added URL for adding a new page
    path('activities/<int:activity_id>/add_question_to_activity/', views.add_question_to_activity, name='add_question_to_activity'),

    # QuestionsBank
    path('courses/<int:course_id>/question_bank/', views.question_bank, name='question_bank'),
    path('courses/<int:course_id>/add_question_to_bank/', views.add_question_to_bank, name='add_question_to_bank'),
    path('questions/<int:question_id>/edit/', views.edit_question_in_bank, name='edit_question_in_bank'),
    path('courses/<int:course_id>/question_type_selection/', views.question_type_selection_for_bank, name='question_type_selection_for_bank'),
    path('courses/<int:course_id>/add_mcq/', views.add_mcq_to_bank, name='add_mcq_to_bank'),
    
    # Additional paths for other activity types as needed

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
