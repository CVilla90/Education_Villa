# Generated by Django 4.0.3 on 2024-10-16 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0018_course_paused'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='is_banned',
            field=models.BooleanField(default=False),
        ),
    ]