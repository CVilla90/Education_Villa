# Portfolio\Education_Villa\edu_core\forms.py

import secrets
import string
import json
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, UserProfile, Certification, Diploma, Course, Lesson, Activity, Question, Option
from django.core.validators import FileExtensionValidator
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _

# Forms here:

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
        fields = ['name', 'description', 'start_date', 'end_date', 'max_attempts', 'unlimited_attempts', 'feedback_visibility']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter activity name', 'required': 'required'}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter activity description', 'required': 'required'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'max_attempts': forms.NumberInput(attrs={'min': 1, 'max': 99}),
        }

    def __init__(self, *args, **kwargs):
        super(ActivityForm, self).__init__(*args, **kwargs)
        # Set initial values for name and description to empty strings
        if not self.instance.pk:
            self.fields['name'].initial = ''
            self.fields['description'].initial = ''

        # Set initial feedback visibility if editing
        if self.instance.pk:
            self.fields['feedback_visibility'].initial = self.instance.feedback_visibility

        # Ensure that the start_date and end_date fields are populated with the stored values
        if self.instance.pk:  
            self.fields['start_date'].initial = self.instance.start_date
            self.fields['end_date'].initial = self.instance.end_date

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("This field is required.")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("This field is required.")
        return description


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text']  # Exclude 'is_correct' field since we handle it separately

# Define a formset with a minimum of 2 options and the ability to add more
OptionFormSet = formset_factory(OptionForm, min_num=2, validate_min=True, extra=1)

class MCQForm(forms.ModelForm):
    key_name = forms.CharField(label="Key Name", required=True)
    randomize_options = forms.BooleanField(label="Randomize Options", required=False, initial=False)
    add_to_bank = forms.BooleanField(label="Add to Course Bank", required=False, initial=True)

    DURING_ASSESSMENT = 'during'
    END_OF_ASSESSMENT = 'end'
    NEVER = 'never'

    FEEDBACK_VISIBILITY_CHOICES = [
        (DURING_ASSESSMENT, _('During Assessment')),
        (END_OF_ASSESSMENT, _('End of Assessment')),
        (NEVER, _('Never')),
    ]

    feedback = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Feedback",
        required=False,
        help_text="Provide feedback that will help the student understand the answer."
    )

    class Meta:
        model = Question
        fields = ['key_name', 'text', 'randomize_options', 'add_to_bank', 'feedback']


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
