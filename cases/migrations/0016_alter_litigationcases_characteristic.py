# Generated by Django 4.2.20 on 2025-04-14 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0015_remove_administrativeinvestigationevent_assignee_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='litigationcases',
            name='characteristic',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='cases.characteristic', verbose_name='Case characteristic'),
            preserve_default=False,
        ),
    ]
