# Generated by Django 4.1.2 on 2022-10-27 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0003_delete_client_type_remove_companies_address_company_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='litigationcases',
            name='detective',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Detective'),
        ),
        migrations.AddField(
            model_name='litigationcases',
            name='judge',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Judge Name'),
        ),
    ]
