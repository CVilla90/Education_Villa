# Generated by Django 4.0.3 on 2024-04-07 21:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0007_activity_structured_content_alter_activity_content_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='activity',
            old_name='content',
            new_name='description',
        ),
    ]
