# Generated by Django 4.2.20 on 2025-05-24 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_alter_contracts_created_by"),
        ("cases", "0020_alter_administrativeinvestigation_created_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="administrativeinvestigation",
            name="paths",
            field=models.ManyToManyField(
                blank=True,
                related_name="AdministrativeInvestigations",
                to="core.path",
                verbose_name="Paths",
            ),
        ),
        migrations.AlterField(
            model_name="folder",
            name="paths",
            field=models.ManyToManyField(
                blank=True, related_name="folders", to="core.path", verbose_name="Paths"
            ),
        ),
        migrations.AlterField(
            model_name="litigationcases",
            name="paths",
            field=models.ManyToManyField(
                blank=True, related_name="cases", to="core.path", verbose_name="Paths"
            ),
        ),
        migrations.AlterField(
            model_name="notation",
            name="paths",
            field=models.ManyToManyField(
                blank=True,
                related_name="notations",
                to="core.path",
                verbose_name="Paths",
            ),
        ),
    ]
