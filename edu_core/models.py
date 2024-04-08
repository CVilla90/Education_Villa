# Portfolio\Education_Villa\edu_core\models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_delete
import os


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


class Activity(models.Model):
    # Activity fields remain largely the same
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    MULTIPLE_CHOICE = 'MCQ'
    TRUE_FALSE = 'TF'
    ESSAY = 'ESSAY'
    # Additional question types as needed

    QUESTION_TYPES = [
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (TRUE_FALSE, 'True or False'),
        (ESSAY, 'Essay'),
        # Add other types here
    ]

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    text = models.TextField()
    options = models.JSONField(blank=True, null=True)  # For MCQs, could store options and correct answer
    correct_answer = models.TextField(blank=True, null=True)  # Could be used for true/false, MCQ, etc.

    def __str__(self):
        return f"{self.text[:50]}..."  # Return first 50 characters of question text


class Grade(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grades')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)


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
