# Generated by Django 4.1.3 on 2022-11-08 07:55

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0014_remove_litigationcases_documents_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='litigationcases',
            name='end_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='litigationcases',
            name='start_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
