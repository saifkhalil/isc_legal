# Generated by Django 4.1.3 on 2023-01-15 06:16

from django.db import migrations, models
import django.db.models.deletion
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pghistory', '0005_events_middlewareevents'),
        ('core', '0005_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatusEvent',
            fields=[
                ('pgh_id', models.AutoField(primary_key=True, serialize=False)),
                ('pgh_created_at', models.DateTimeField(auto_now_add=True)),
                ('pgh_label', models.TextField(help_text='The event label.')),
                ('id', models.IntegerField()),
                ('status', models.CharField(max_length=250, verbose_name='Status')),
            ],
            options={
                'abstract': False,
            },
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='status',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "core_statusevent" ("id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "status") VALUES (NEW."id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."status"); RETURN NULL;', hash='cb8f4753b6405749f4124f1d18c1f1290856949a', operation='INSERT', pgid='pgtrigger_snapshot_insert_0f7bb', table='core_status', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='status',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "core_statusevent" ("id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "status") VALUES (NEW."id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."status"); RETURN NULL;', hash='2694667a700e74f109c508272de3326821aa1b28', operation='UPDATE', pgid='pgtrigger_snapshot_update_eb6d5', table='core_status', when='AFTER')),
        ),
        migrations.AddField(
            model_name='statusevent',
            name='pgh_context',
            field=models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='pghistory.context'),
        ),
        migrations.AddField(
            model_name='statusevent',
            name='pgh_obj',
            field=models.ForeignKey(db_constraint=False, on_delete=django.db.models.deletion.DO_NOTHING, related_name='event', to='core.status'),
        ),
    ]