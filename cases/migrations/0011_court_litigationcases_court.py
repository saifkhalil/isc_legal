# Generated by Django 4.1.2 on 2022-10-30 08:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0010_litigationcases_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='court',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=250, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Court',
                'verbose_name_plural': 'Courts',
            },
        ),
        migrations.AddField(
            model_name='litigationcases',
            name='court',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cases.court', verbose_name='Court name'),
        ),
    ]
