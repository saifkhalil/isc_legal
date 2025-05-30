# Generated by Django 4.2.20 on 2025-05-24 08:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("activities", "0007_alter_hearing_created_by_alter_task_created_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="task",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tasks_createdby",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
