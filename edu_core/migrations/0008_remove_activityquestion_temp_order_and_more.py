# Generated by Django 4.0.3 on 2024-08-27 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edu_core', '0007_activityquestion_temp_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activityquestion',
            name='temp_order',
        ),
        migrations.AlterField(
            model_name='activityquestion',
            name='page_number',
            field=models.IntegerField(default=1),
        ),
    ]
