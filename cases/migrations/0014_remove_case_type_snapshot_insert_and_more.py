# Generated by Django 4.1.3 on 2024-09-05 06:38

from django.db import migrations, models
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0013_alter_litigationcases_case_close_status_and_more'),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name='case_type',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='case_type',
            name='snapshot_update',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='stages',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='stages',
            name='snapshot_update',
        ),
        migrations.AddField(
            model_name='case_type',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='casetypeevent',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='stages',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='stagesevent',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='case_type',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "cases_casetypeevent" ("id", "is_deleted", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "type") VALUES (NEW."id", NEW."is_deleted", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."type"); RETURN NULL;', hash='582e970980d37043df6533990c69043a0348fe28', operation='INSERT', pgid='pgtrigger_snapshot_insert_0bd9c', table='cases_case_type', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='case_type',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "cases_casetypeevent" ("id", "is_deleted", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "type") VALUES (NEW."id", NEW."is_deleted", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."type"); RETURN NULL;', hash='fa724d93f47a32d3bc65e064265755a0da143cc1', operation='UPDATE', pgid='pgtrigger_snapshot_update_35c45', table='cases_case_type', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='stages',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "cases_stagesevent" ("id", "is_deleted", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."id", NEW."is_deleted", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='f2dbb256b10a2755b6ac276347030bbea4d8b5d8', operation='INSERT', pgid='pgtrigger_snapshot_insert_e8403', table='cases_stages', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='stages',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "cases_stagesevent" ("id", "is_deleted", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."id", NEW."is_deleted", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='b5b68ecd7b9629acda41bcd51375fe89df10034d', operation='UPDATE', pgid='pgtrigger_snapshot_update_7b495', table='cases_stages', when='AFTER')),
        ),
    ]
