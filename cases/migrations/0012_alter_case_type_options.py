# Generated by Django 4.1.2 on 2022-10-31 07:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0011_court_litigationcases_court'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case_type',
            options={'verbose_name': 'Case Type', 'verbose_name_plural': 'Case Types'},
        ),
    ]