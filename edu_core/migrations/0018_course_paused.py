# Generated by Django 4.0.3 on 2024-10-16 02:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0017_registration_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='paused',
            field=models.BooleanField(default=False),
        ),
    ]
