# Generated by Django 4.0.3 on 2024-10-11 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0016_course_is_public_alter_activity_max_attempts'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('professor', 'Professor')], default='student', max_length=10),
        ),
    ]