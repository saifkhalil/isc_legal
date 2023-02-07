# Generated by Django 4.1.3 on 2023-01-30 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_remove_path_snapshot_insert_and_more'),
        ('cases', '0009_alter_litigationcases_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='litigationcases',
            name='Paths',
            field=models.ManyToManyField(blank=True, null=True, to='core.path', verbose_name='Paths'),
        ),
        migrations.AlterField(
            model_name='litigationcases',
            name='documents',
            field=models.ManyToManyField(blank=True, to='core.documents', verbose_name='Documents'),
        ),
    ]