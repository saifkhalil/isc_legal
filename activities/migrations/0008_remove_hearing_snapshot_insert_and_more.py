# Generated by Django 4.1.3 on 2023-03-06 06:26

from django.db import migrations
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0007_remove_hearing_snapshot_insert_and_more'),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name='hearing',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='hearing',
            name='snapshot_update',
        ),
        migrations.RenameField(
            model_name='hearing',
            old_name='latset',
            new_name='latest',
        ),
        migrations.RenameField(
            model_name='hearingevent',
            old_name='latset',
            new_name='latest',
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='hearing',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "folder_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "latest", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."folder_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."latest", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='f9b21f803b036f0812d6990a168ff49885c83ddc', operation='INSERT', pgid='pgtrigger_snapshot_insert_28885', table='activities_hearing', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='hearing',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "folder_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "latest", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."folder_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."latest", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='58c9e272cebf76742f95a542bc230f1ac7a17ea5', operation='UPDATE', pgid='pgtrigger_snapshot_update_94291', table='activities_hearing', when='AFTER')),
        ),
    ]