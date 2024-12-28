# Education_Villa\edu_core\models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.core.exceptions import ValidationError
import os, json
from django.core.validators import URLValidator
from urllib.parse import urlparse


class CustomUser(AbstractUser):
    # User roles
    STUDENT = 'student'
    PROFESSOR = 'professor'
    MODERATOR = 'moderator'
    USER_TYPE_CHOICES = [
        (STUDENT, 'Student'),
        (PROFESSOR, 'Professor'),
        (MODERATOR, 'Moderator'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default=STUDENT)


def validate_trusted_url(value):
    allowed_domains = [
        'imgur.com',                # Imgur
        'i.imgur.com',              # Direct Imgur images
        'drive.google.com',         # Google Drive (file sharing links)
        'drive.googleusercontent.com', # Google Drive direct image hosting
        'dropbox.com',              # Dropbox
        'youtube.com',              # YouTube full links
        'youtu.be',                 # YouTube short links
        'facebook.com',             # Facebook
        'fbcdn.net',                # Facebook's CDN
        'instagram.com',            # Instagram
        'cdninstagram.com',         # Instagram CDN
        'flickr.com',               # Flickr
        'live.staticflickr.com',    # Flickr CDN
        'deviantart.com',           # DeviantArt
        'cdn.discordapp.com',       # Discord image hosting
        'unsplash.com',             # Unsplash free images
        'pexels.com',               # Pexels free images
        'soundcloud.com',           # SoundCloud
        'w.soundcloud.com',         # SoundCloud embedded player
    ]
    
    # Validate if the URL belongs to one of the allowed domains
    if not any(domain in value for domain in allowed_domains):
        raise ValidationError(f"URL must be from one of the trusted domains: {', '.join(allowed_domains)}")
    

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.URLField(
        max_length=500, null=True, blank=True, 
        help_text="Paste a URL to your profile picture",
        validators=[validate_trusted_url]
    )

    def get_profile_picture_direct_url(self):
        if 'drive.google.com' in self.profile_picture:
            file_id = self.profile_picture.split('/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?id={file_id}"
        return self.profile_picture


class Certification(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='certifications')
    image_url = models.URLField(
        max_length=500, null=True, blank=True,
        help_text="Paste a URL to the certification image",
        validators=[validate_trusted_url]
    )
    description = models.CharField(max_length=255, null=True, blank=True)  # Ensure this exists


class Course(models.Model):
    name = models.CharField(max_length=255)
    creation_date = models.DateField(auto_now_add=True)
    last_update_date = models.DateField(auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'user_type': CustomUser.PROFESSOR}, related_name='authored_courses')
    students = models.ManyToManyField(CustomUser, through='Registration', related_name='registered_courses')
    image_url = models.URLField(
        max_length=500, null=True, blank=True,
        help_text="Paste a URL to the course image",
        validators=[validate_trusted_url]
    )
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=True)  # New field for public visibility
    paused = models.BooleanField(default=False)


class CourseCorpus(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='corpus')
    file = models.FileField(upload_to='course_corpus/')
    upload_date = models.DateTimeField(auto_now_add=True)
    

@receiver(post_delete, sender=Course)
def auto_delete_course_files_on_delete(sender, instance, **kwargs):
    """
    Deletes files from the filesystem
    when a Course object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
            

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    name = models.CharField(max_length=255)
    content = models.TextField()


class Question(models.Model):
    MULTIPLE_CHOICE = 'MCQ'
    TRUE_FALSE = 'TF'
    ESSAY = 'ESSAY'
    CONTENT_BLOCK = 'CONTENT_BLOCK'

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (TRUE_FALSE, 'True or False'),
        (ESSAY, 'Essay'),
        (CONTENT_BLOCK, 'Content Block'),
    ]

    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='activity_questions', null=True, blank=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_questions')
    text = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    image_url = models.URLField(
        validators=[validate_trusted_url],
        blank=True,
        null=True,
        help_text="URL for question images"
    )
    yt_video_link = models.URLField(validators=[validate_trusted_url], blank=True, null=True)
    file_url = models.URLField(
        validators=[validate_trusted_url],
        blank=True,
        null=True,
        help_text="URL for question files"
    )
    correct_answer = models.TextField(blank=True, null=True)
    randomize_options = models.BooleanField(default=False)
    key_name = models.CharField(max_length=255, blank=True, null=True)
    in_bank = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        text_snippet = self.text[:50] if self.text else ''
        content_snippet = self.content[:50] if self.content else ''
        return text_snippet or content_snippet or "Empty Question"


class Activity(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    questions = models.ManyToManyField(Question, through='ActivityQuestion', related_name='activity_set')

    FEEDBACK_VISIBILITY_CHOICES = [
        ('never', 'Never'),
        ('during', 'During Assessment'),
        ('end', 'End of Assessment'),
        ('always', 'Always')
    ]
    feedback_visibility = models.CharField(
        max_length=10,
        choices=FEEDBACK_VISIBILITY_CHOICES,
        default='never',
        help_text="Choose when to show feedback for all questions in this activity."
    )

    # New Fields
    max_attempts = models.PositiveIntegerField(blank=True, null=True, default=1, help_text="Set the maximum number of attempts allowed.")
    unlimited_attempts = models.BooleanField(default=False, help_text="Allow unlimited attempts if checked.")

    def __str__(self):
        return self.name


class ActivityAttempt(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attempts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'activity', 'created_at')


class ActivityQuestion(models.Model):
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE)
    question = models.ForeignKey('Question', on_delete=models.CASCADE, null=True, blank=True)
    order = models.IntegerField(default=0)
    page_number = models.IntegerField(default=1)
    is_separator = models.BooleanField(default=False)

    class Meta:
        unique_together = ('activity', 'order')
        ordering = ['order']

    def __str__(self):
        if self.is_separator:
            return f"Page Separator (Page {self.page_number})"
        if self.question and self.question.text:
            return f"Question: {self.question.text[:50]}"
        return "Missing Question"


class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Grade(models.Model):
    student = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='grades')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically sets the time when the grade is created

    def __str__(self):
        return f"{self.student.username} - {self.activity.name} - {self.score}"


class Registration(models.Model):
    STUDENT = 'student'
    PROFESSOR = 'professor'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (PROFESSOR, 'Professor'),
    ]
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='course_registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    is_banned = models.BooleanField(default=False) 


@receiver(models.signals.post_delete, sender=UserProfile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.profile_picture:
        if os.path.isfile(instance.profile_picture.path):
            os.remove(instance.profile_picture.path)


# Add necessary signals for cleaning up Certification images if required


class Diploma(models.Model):
    course_name = models.CharField(max_length=255)
    student_name = models.CharField(max_length=255)  # Changed from ForeignKey to CharField
    issue_date = models.DateField()
    verification_key = models.CharField(max_length=255, unique=True)
    issued_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='diplomas_issued')

    def __str__(self):
        return f"{self.course_name} - {self.student_name}"  # Changed from student.username to student_name
