# Portfolio\Education_Villa\edu_core\urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

# User Views
from .views.user_views import profile, edit_profile, SignUpView

# Utility Views
from .views.utility_views import home

# Course Views
from .views.course_views import (
    create_course, course_detail, delete_course, edit_course, register_course, course_dashboard
)

# Lesson Views
from .views.lesson_views import lesson_add, lesson_view, delete_lesson, lesson_dashboard

# Activity CRUD Views
from .views.activity_crud_views import activity_add, delete_activity, edit_activity

# Activity Viewing Views
from .views.activity_viewing_views import activity_view, upload_image

# Activity Question Views
from .views.activity_question_views import (
    add_mcq, add_content_block, question_type_selection, select_from_bank,
    add_question_to_activity, reorder_questions, add_page,
    move_question_up, move_question_down, remove_question, remove_page,
    mcq_parser
)

# Activity Dashboard Views
from .views.activity_dashboard_views import activity_dashboard, delete_attempt

# AI Professor Views
from .views.ai_professor_views import ai_course_professor, delete_corpus_file

# Diploma Views
from .views.diploma_views import diploma_search, view_diploma_online, download_diploma_pdf, create_diploma

# Question Bank Views
from .views.question_bank_views import (
    question_bank, add_question_to_bank, edit_mcq_from_bank, question_type_selection_for_bank,
    add_mcq_to_bank, add_content_block_to_bank, edit_question, delete_question
)

urlpatterns = [
    # Landing
    path('', home, name='home'),

    # Authentication
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # User Profile
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    # Diploma Management
    path('diploma/search/', diploma_search, name='diploma_search'),
    path('diploma/view/<int:pk>/', view_diploma_online, name='view_diploma'),
    path('diploma/download/<str:verification_key>/', download_diploma_pdf, name='download_diploma_pdf'),
    path('diploma/create/', create_diploma, name='create_diploma'),

    # Course Management
    path('create-course/', create_course, name='create_course'),
    path('courses/<int:course_id>/', course_detail, name='course_detail'),
    path('courses/delete/<int:pk>/', delete_course, name='delete_course'),
    path('courses/edit/<int:course_id>/', edit_course, name='edit_course'),
    path('courses/<int:course_id>/register/', register_course, name='register_course'),
    path('course/<int:course_id>/dashboard/', course_dashboard, name='course_dashboard'),

    # AI Course Professor URL
    path('courses/<int:course_id>/ai_professor/', ai_course_professor, name='ai_course_professor'),
    path('corpus/<int:corpus_id>/delete/', delete_corpus_file, name='delete_corpus_file'),

    # Lesson Management
    path('courses/<int:course_id>/lesson_add/', lesson_add, name='lesson_add'),    
    path('lessons/<int:lesson_id>/', lesson_view, name='lesson_view'),
    path('lessons/<int:lesson_id>/delete/', delete_lesson, name='delete_lesson'),
    path('lessons/<int:lesson_id>/dashboard/', lesson_dashboard, name='lesson_dashboard'), 

    # Activity Management (activity_views.py)
    path('lessons/<int:lesson_id>/activity_add/', activity_add, name='activity_add'),
    path('activities/<int:activity_id>/delete/', delete_activity, name='delete_activity'),
    path('activities/<int:activity_id>/edit/', edit_activity, name='edit_activity'),

    # Activity Viewing (activity_viewing_views.py)
    path('activities/<int:activity_id>/', activity_view, name='activity_view'),
    path('upload_image/', upload_image, name='upload_image'),

    # Activity Question Management (activity_question_views.py)
    path('activities/<int:activity_id>/add_mcq/', add_mcq, name='add_mcq'),
    path('activities/<int:activity_id>/mcq_parser/', mcq_parser, name='activity_mcq_parser'),  # For activity
    path('courses/<int:course_id>/mcq_parser/', mcq_parser, name='course_mcq_parser'),  # For question bank
    path('activities/<int:activity_id>/add_content_block/', add_content_block, name='add_content_block'),    
    path('activities/<int:activity_id>/question_type_selection/', question_type_selection, name='question_type_selection'),
    path('activities/<int:activity_id>/select_from_bank/', select_from_bank, name='select_from_bank'),
    path('activities/<int:activity_id>/reorder_questions/', reorder_questions, name='activity_reorder_questions'),
    path('activities/<int:activity_id>/add_page/', add_page, name='activity_add_page'),
    path('activities/<int:activity_id>/add_question_to_activity/', add_question_to_activity, name='activity_add_question'),
    path('activities/<int:activity_id>/move_question_up/', move_question_up, name='activity_move_question_up'),
    path('activities/<int:activity_id>/move_question_down/', move_question_down, name='activity_move_question_down'),
    path('activities/<int:activity_id>/remove_question/', remove_question, name='activity_remove_question'),
    path('activities/<int:activity_id>/remove_page/', remove_page, name='activity_remove_page'),

    # Activity Dashboard (activity_dashboard_views.py)
    path('activities/<int:activity_id>/dashboard/', activity_dashboard, name='activity_dashboard'),
    path('attempts/<int:attempt_id>/delete/', delete_attempt, name='delete_attempt'),

    # Questions Bank (question_bank_views.py)
    path('courses/<int:course_id>/question_bank/', question_bank, name='question_bank'),
    path('courses/<int:course_id>/add_question_to_bank/', add_question_to_bank, name='add_question_to_bank'),
    #path('questions/<int:question_id>/edit/', edit_mcq_from_bank, name='edit_question_in_bank'),
    path('courses/<int:course_id>/question_type_selection/', question_type_selection_for_bank, name='question_type_selection_for_bank'),
    path('courses/<int:course_id>/add_mcq/', add_mcq_to_bank, name='add_mcq_to_bank'),
    path('courses/<int:course_id>/add_content_block_to_bank/', add_content_block_to_bank, name='add_content_block_to_bank'),
    path('questions/<int:question_id>/edit/', edit_question, name='edit_question'),
    path('questions/<int:question_id>/delete/', delete_question, name='delete_question'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)