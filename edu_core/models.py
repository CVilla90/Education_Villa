# Portfolio\Education_Villa\edu_core\models.py

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


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            old_profile_picture = UserProfile.objects.get(id=self.id).profile_picture
            if old_profile_picture and self.profile_picture != old_profile_picture:
                if os.path.isfile(old_profile_picture.path):
                    os.remove(old_profile_picture.path)
        except UserProfile.DoesNotExist:
            pass
        super(UserProfile, self).save(*args, **kwargs)


class Certification(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='certifications')
    image = models.ImageField(upload_to='certifications/')
    description = models.CharField(max_length=255, null=True, blank=True)


class Course(models.Model):
    name = models.CharField(max_length=255)
    creation_date = models.DateField(auto_now_add=True)
    last_update_date = models.DateField(auto_now=True)
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'user_type': CustomUser.PROFESSOR}, related_name='authored_courses')
    students = models.ManyToManyField(CustomUser, through='Registration', related_name='registered_courses')
    image = models.ImageField(upload_to='course_images/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=True)  # New field for public visibility
    paused = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.pk:
            old_image = Course.objects.get(pk=self.pk).image
            if old_image and self.image != old_image:
                if os.path.isfile(old_image.path):
                    os.remove(old_image.path)
        super(Course, self).save(*args, **kwargs)


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
    CONTENT_BLOCK = 'CONTENT_BLOCK'  # New type

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
    image = models.ImageField(upload_to='content_blocks/', null=True, blank=True)
    yt_video_link = models.URLField(validators=[URLValidator()], blank=True, null=True)
    file_upload = models.FileField(upload_to='content_block_files/', null=True, blank=True)
    correct_answer = models.TextField(blank=True, null=True)
    randomize_options = models.BooleanField(default=False)
    key_name = models.CharField(max_length=255, blank=True, null=True)
    in_bank = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        text_snippet = self.text[:50] if self.text else ''
        content_snippet = self.content[:50] if self.content else ''
        return text_snippet or content_snippet or "Empty Question"

    def save(self, *args, **kwargs):
        # Handle old image removal when updating the image
        try:
            old_image = Question.objects.get(id=self.id).image
            if old_image and self.image != old_image:
                if os.path.isfile(old_image.path):
                    os.remove(old_image.path)
        except Question.DoesNotExist:
            pass
        super(Question, self).save(*args, **kwargs)


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
