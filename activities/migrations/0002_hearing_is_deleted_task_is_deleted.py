# Generated by Django 4.1.3 on 2022-11-13 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hearing',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='task',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
    ]
