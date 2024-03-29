# Generated by Django 4.1.3 on 2023-01-14 18:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_status"),
        ("activities", "0016_alter_hearing_hearing_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hearing",
            name="hearing_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_hearing_status",
                to="core.status",
                verbose_name="Hearing Status",
            ),
        ),
        migrations.AlterField(
            model_name="hearingevent",
            name="hearing_status",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="core.status",
                verbose_name="Hearing Status",
            ),
        ),
        migrations.AlterField(
            model_name="task",
            name="task_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_task_status",
                to="core.status",
                verbose_name="Task Status",
            ),
        ),
        migrations.AlterField(
            model_name="taskevent",
            name="task_status",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="core.status",
                verbose_name="Task Status",
            ),
        ),
    ]
