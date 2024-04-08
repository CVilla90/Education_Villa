# Generated by Django 4.0.3 on 2024-04-07 22:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0008_rename_content_activity_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='structured_content',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='type',
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.CharField(choices=[('MCQ', 'Multiple Choice'), ('TF', 'True or False'), ('ESSAY', 'Essay')], max_length=50)),
                ('text', models.TextField()),
                ('options', models.JSONField(blank=True, null=True)),
                ('correct_answer', models.TextField(blank=True, null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='edu_core.activity')),
            ],
        ),
    ]
