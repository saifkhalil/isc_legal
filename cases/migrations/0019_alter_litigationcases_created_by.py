# Generated by Django 4.2.20 on 2025-05-20 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0018_alter_importantdevelopment_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="litigationcases",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cases_createdby",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Created At",
            ),
        ),
    ]
