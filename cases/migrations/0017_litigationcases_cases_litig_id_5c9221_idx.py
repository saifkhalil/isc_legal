# Generated by Django 4.1.3 on 2022-11-16 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0016_litigationcases_is_deleted'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='litigationcases',
            index=models.Index(fields=['id', 'name', 'Stage', 'case_type', 'case_category', 'assignee', 'court', 'description'], name='cases_litig_id_5c9221_idx'),
        ),
    ]
