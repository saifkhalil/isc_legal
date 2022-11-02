# Generated by Django 4.1.2 on 2022-10-11 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_comments_id_alter_priorities_id'),
        ('cases', '0006_alter_litigationcases_stage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='litigationcases',
            name='comments',
            field=models.ManyToManyField(blank=True, to='core.comments', verbose_name='Comments'),
        ),
        migrations.AlterField(
            model_name='litigationcases',
            name='due_date',
            field=models.DateField(blank=True, null=True, verbose_name='Due date'),
        ),
        migrations.AlterField(
            model_name='litigationcases',
            name='filed_on',
            field=models.DateField(blank=True, null=True, verbose_name='Filed on'),
        ),
    ]
