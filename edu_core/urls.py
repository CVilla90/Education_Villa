# Portfolio\Education_Villa\edu_core\urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views.user_views import profile, edit_profile, SignUpView
from .views.activity_views import (
    activity_add, delete_activity, activity_view, add_mcq, question_type_selection,
    select_from_bank, edit_activity, reorder_questions, add_page, add_question_to_activity
)
from .views.course_views import create_course, course_detail, delete_course, edit_course
from .views.lesson_views import lesson_add, lesson_view, delete_lesson
from .views.diploma_views import (
    diploma_search, view_diploma_online, download_diploma_pdf, create_diploma
)
from .views.utility_views import home  # Make sure the home view is in the correct file
from .views.question_bank_views import (
    question_bank, add_question_to_bank, edit_question_in_bank, question_type_selection_for_bank, add_mcq_to_bank
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

    # Lesson Management
    path('courses/<int:course_id>/lesson_add/', lesson_add, name='lesson_add'),    
    path('lessons/<int:lesson_id>/', lesson_view, name='lesson_view'),
    path('lessons/<int:lesson_id>/delete/', delete_lesson, name='delete_lesson'),

    # Activity Management
    path('lessons/<int:lesson_id>/activity_add/', activity_add, name='activity_add'),
    path('activities/<int:activity_id>/delete/', delete_activity, name='delete_activity'),
    path('activities/<int:activity_id>/', activity_view, name='activity_view'),
    path('activities/<int:activity_id>/add_mcq/', add_mcq, name='add_mcq'),
    path('activities/<int:activity_id>/question_type_selection/', question_type_selection, name='question_type_selection'),
    path('activities/<int:activity_id>/select_from_bank/', select_from_bank, name='select_from_bank'),
    path('activities/<int:activity_id>/edit/', edit_activity, name='edit_activity'),
    path('activities/<int:activity_id>/reorder_questions/', reorder_questions, name='reorder_questions'),
    path('activities/<int:activity_id>/add_page/', add_page, name='add_page'),
    path('activities/<int:activity_id>/add_question_to_activity/', add_question_to_activity, name='add_question_to_activity'),

    # QuestionsBank
    path('courses/<int:course_id>/question_bank/', question_bank, name='question_bank'),
    path('courses/<int:course_id>/add_question_to_bank/', add_question_to_bank, name='add_question_to_bank'),
    path('questions/<int:question_id>/edit/', edit_question_in_bank, name='edit_question_in_bank'),
    path('courses/<int:course_id>/question_type_selection/', question_type_selection_for_bank, name='question_type_selection_for_bank'),
    path('courses/<int:course_id>/add_mcq/', add_mcq_to_bank, name='add_mcq_to_bank'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
