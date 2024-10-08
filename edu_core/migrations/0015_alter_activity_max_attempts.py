# Generated by Django 4.0.3 on 2024-10-07 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0014_rename_maximum_attempts_activity_max_attempts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='max_attempts',
            field=models.PositiveIntegerField(blank=True, help_text='Set the maximum number of attempts allowed.', null=True),
        ),
    ]