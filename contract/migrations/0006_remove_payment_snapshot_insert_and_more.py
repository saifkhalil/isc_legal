# Generated by Django 4.1.3 on 2024-06-26 10:01

from django.db import migrations, models
import django.db.models.deletion
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contract', '0005_reminder_modified_at_reminder_modified_by'),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name='payment',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='payment',
            name='snapshot_update',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='payments',
        ),
        migrations.AddField(
            model_name='payment',
            name='contract',
            field=models.ForeignKey(default=34, on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='contract.contract', verbose_name='Contract'),
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='contract',
            field=models.ForeignKey(db_constraint=False, default=34, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='contract.contract', verbose_name='Contract'),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='payment',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "contract_paymentevent" ("amount", "contract_id", "created_at", "created_by_id", "date", "duration_id", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."amount", NEW."contract_id", NEW."created_at", NEW."created_by_id", NEW."date", NEW."duration_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='c24ca11f77c7b824b0136c8d03e31b5324b89eab', operation='INSERT', pgid='pgtrigger_snapshot_insert_2d876', table='contract_payment', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='payment',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "contract_paymentevent" ("amount", "contract_id", "created_at", "created_by_id", "date", "duration_id", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."amount", NEW."contract_id", NEW."created_at", NEW."created_by_id", NEW."date", NEW."duration_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='fa007473e45c6dcef65138ba0532036272b3bf45', operation='UPDATE', pgid='pgtrigger_snapshot_update_9e0bc', table='contract_payment', when='AFTER')),
        ),
    ]
