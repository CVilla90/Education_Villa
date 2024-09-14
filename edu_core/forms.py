# Portfolio\Education_Villa\edu_core\forms.py

import secrets
import string
import json
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile, Certification, Diploma, Course, Lesson, Activity, Question
from django.core.validators import FileExtensionValidator

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
        fields = ['name', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)

        # Ensure that the start_date and end_date fields are populated with the stored values
        if self.instance.pk:  # Check if the instance exists (i.e., the form is in edit mode)
            self.fields['start_date'].initial = self.instance.start_date
            self.fields['end_date'].initial = self.instance.end_date


class MCQForm(forms.Form):
    key_name = forms.CharField(label="Key Name", required=True)  # Add KeyName field
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
    randomize_options = forms.BooleanField(
        label="Randomize Options",
        required=False,
        initial=False,
    )

    add_to_bank = forms.BooleanField(
        label="Add to Course Bank",
        required=False,
        initial=True,  # Checked by default
    )


class ContentBlockForm(forms.ModelForm):
    key_name = forms.CharField(label="Key Name", required=True)
    content = forms.CharField(widget=forms.Textarea, label="Content Text", required=False)
    image = forms.ImageField(required=False, label="Upload Image")
    yt_video_link = forms.URLField(required=False, label="YouTube Video Link", help_text="Paste a YouTube link to embed the video.")
    file_upload = forms.FileField(
        required=False,
        label="Upload File",
        help_text="Upload a document or audio file.",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'mp3', 'wav', 'm4a'])]
    )
    in_bank = forms.BooleanField(
        label="Add to Course Bank",
        required=False,
        initial=True,  # Checked by default
    )

    class Meta:
        model = Question
        fields = ['key_name', 'content', 'image', 'yt_video_link', 'file_upload', 'in_bank']


class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['key_name', 'question_type', 'text', 'correct_answer', 'randomize_options', 'in_bank']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'key_name': forms.TextInput(attrs={'placeholder': 'Enter a descriptive key name'}),
        }

    def __init__(self, *args, **kwargs):
        super(QuestionBankForm, self).__init__(*args, **kwargs)
        # Set initial value for 'in_bank' to True
        self.fields['in_bank'].initial = True
        # Custom placeholder for key_name
        self.fields['key_name'].widget.attrs.update({'placeholder': 'Key Name (optional)'})
