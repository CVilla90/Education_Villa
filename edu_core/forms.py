# Portfolio\Education_Villa\edu_core\forms.py
import secrets
import string
import json

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile, Certification, Diploma, Course, Lesson, Activity, Question

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)  # Updated to include first_name and last_name

# Form for creating diplomas
def generate_random_verification_key(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['image', 'description']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'image', 'description']


class DiplomaForm(forms.ModelForm):
    class Meta:
        model = Diploma
        fields = ['course_name', 'student_name', 'issue_date', 'verification_key']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            # Note: The placeholder will be redundant but is left here for consistency
            'verification_key': forms.TextInput(attrs={'placeholder': 'Verification Key'}),
        }

    def __init__(self, *args, **kwargs):
        super(DiplomaForm, self).__init__(*args, **kwargs)
        # Set initial value for 'verification_key' to a randomly generated key
        self.fields['verification_key'].initial = generate_random_verification_key()
        # Other field customizations
        self.fields['course_name'].widget.attrs.update({'placeholder': 'Course Name'})
        self.fields['student_name'].widget.attrs.update({'placeholder': 'Student Name'})


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['name', 'content']


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description']  


class MCQForm(forms.Form):
    # No longer a ModelForm since we're not directly creating or updating a model instance in this form
    question_text = forms.CharField(widget=forms.Textarea, label="Question Text")
    option_1 = forms.CharField(label="Option 1")
    option_2 = forms.CharField(label="Option 2")
    option_3 = forms.CharField(label="Option 3", required=False)  # Optional
    option_4 = forms.CharField(label="Option 4", required=False)  # Optional
    correct_answer = forms.ChoiceField(choices=[
        ("option_1", "Option 1"),
        ("option_2", "Option 2"),
        ("option_3", "Option 3"),
        ("option_4", "Option 4")],
        label="Correct Answer"
    )

        