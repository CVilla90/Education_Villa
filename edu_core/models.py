# Portfolio\Education_Villa\edu_core\models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.core.exceptions import ValidationError
import os, json


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
    description = models.TextField(null=True, blank=True)  # New field for course description
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_image = Course.objects.get(pk=self.pk).image
            if old_image and self.image != old_image:
                if os.path.isfile(old_image.path):
                    os.remove(old_image.path)
        super(Course, self).save(*args, **kwargs)


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

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (TRUE_FALSE, 'True or False'),
        (ESSAY, 'Essay'),
        # Add other types here
    ]

    # Change related_name to avoid conflicts
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='activity_questions', null=True, blank=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='course_questions')
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    text = models.TextField()
    correct_answer = models.TextField(blank=True, null=True)
    randomize_options = models.BooleanField(default=False)
    key_name = models.CharField(max_length=255, blank=True, null=True)
    in_bank = models.BooleanField(default=False)  # This is the correct field name

    def __str__(self):
        return self.text[:50]


class Activity(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    questions = models.ManyToManyField(Question, through='ActivityQuestion', related_name='activity_set')

    def __str__(self):
        return self.name


class ActivityQuestion(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ('activity', 'question')
        ordering = ['order']

    def __str__(self):
        return f"{self.activity.name} - {self.question.text[:50]}"


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
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='course_registrations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateField(auto_now_add=True)


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
