# Generated by Django 4.1.3 on 2023-01-16 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0019_path_pathevent_remove_directoryevent_created_by_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="path",
            options={"verbose_name": "Path", "verbose_name_plural": "Paths"},
        ),
        migrations.AlterField(
            model_name="path",
            name="documents",
            field=models.ManyToManyField(
                blank=True,
                related_name="paths",
                to="core.documents",
                verbose_name="Documents",
            ),
        ),
    ]
