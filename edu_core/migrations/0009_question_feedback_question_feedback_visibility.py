# Generated by Django 4.0.3 on 2024-10-06 17:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0008_coursecorpus'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='feedback',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='question',
            name='feedback_visibility',
            field=models.CharField(choices=[('during', 'During Assessment'), ('end', 'End of Assessment'), ('never', 'Never')], default='never', max_length=20),
        ),
    ]
