# Generated by Django 4.1.2 on 2022-11-02 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_documents_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='documents',
            name='case_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='Litigation Case'),
        ),
    ]
