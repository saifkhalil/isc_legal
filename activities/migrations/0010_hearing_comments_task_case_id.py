# Generated by Django 4.1.3 on 2022-11-08 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_contracts_attachment_and_more'),
        ('activities', '0009_rename_assigned_task_assignee'),
    ]

    operations = [
        migrations.AddField(
            model_name='hearing',
            name='comments',
            field=models.ManyToManyField(blank=True, to='core.comments', verbose_name='Comments'),
        ),
        migrations.AddField(
            model_name='task',
            name='case_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Litigation Case'),
        ),
    ]
