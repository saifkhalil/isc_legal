# Generated by Django 4.1.3 on 2023-02-12 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_path_name_alter_pathevent_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='path',
            name='name',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='pathevent',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
