# Generated by Django 4.1.2 on 2022-10-12 10:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0002_event_comments_remove_hearing_comments_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='eid',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Event ID'),
        ),
    ]
