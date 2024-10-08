# Generated by Django 4.0.3 on 2024-10-07 02:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0011_alter_activity_feedback_visibility'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='max_attempts',
            field=models.PositiveIntegerField(blank=True, help_text='Maximum number of attempts allowed (leave blank for no limit).', null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='unlimited_attempts',
            field=models.BooleanField(default=True, help_text='Check to allow unlimited attempts.'),
        ),
        migrations.CreateModel(
            name='ActivityAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='edu_core.activity')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'activity', 'created_at')},
            },
        ),
    ]
