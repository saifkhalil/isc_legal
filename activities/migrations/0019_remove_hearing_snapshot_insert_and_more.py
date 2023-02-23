# Generated by Django 4.1.3 on 2023-01-25 11:06

from django.db import migrations, models
import django.db.models.deletion
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cases', '0029_remove_folder_hearing_remove_folder_tasks_and_more'),
        ('activities', '0018_remove_hearing_snapshot_insert_and_more'),
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
        pgtrigger.migrations.RemoveTrigger(
            model_name='task',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='task',
            name='snapshot_update',
        ),
        migrations.AlterField(
            model_name='hearing',
            name='case_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cases.litigationcases', verbose_name='Litigation Case'),
        ),
        migrations.AlterField(
            model_name='hearing',
            name='folder_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cases.folder', verbose_name='Folder'),
        ),
        migrations.AlterField(
            model_name='hearingevent',
            name='case_id',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='cases.litigationcases', verbose_name='Litigation Case'),
        ),
        migrations.AlterField(
            model_name='hearingevent',
            name='folder_id',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='cases.folder', verbose_name='Folder'),
        ),
        migrations.AlterField(
            model_name='task',
            name='case_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cases.litigationcases', verbose_name='Litigation Case'),
        ),
        migrations.AlterField(
            model_name='task',
            name='folder_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cases.folder', verbose_name='Folder'),
        ),
        migrations.AlterField(
            model_name='taskevent',
            name='case_id',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='cases.litigationcases', verbose_name='Litigation Case'),
        ),
        migrations.AlterField(
            model_name='taskevent',
            name='folder_id',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to='cases.folder', verbose_name='Folder'),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='hearing',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "folder_id_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."folder_id_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='7adc03051a6c94207f116641d7085362f435a388', operation='INSERT', pgid='pgtrigger_snapshot_insert_28885', table='activities_hearing', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='hearing',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "folder_id_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."folder_id_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;', hash='b118c82694e1ead0ad2a77219b42a573989c578b', operation='UPDATE', pgid='pgtrigger_snapshot_update_94291', table='activities_hearing', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='task',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "activities_taskevent" ("assignee_id", "case_id_id", "created_at", "created_by_id", "description", "due_date", "folder_id_id", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "task_status_id", "title") VALUES (NEW."assignee_id", NEW."case_id_id", NEW."created_at", NEW."created_by_id", NEW."description", NEW."due_date", NEW."folder_id_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."task_status_id", NEW."title"); RETURN NULL;', hash='59a45ea471eae509e79485901494ad9f63f8f707', operation='INSERT', pgid='pgtrigger_snapshot_insert_0cb53', table='activities_task', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='task',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "activities_taskevent" ("assignee_id", "case_id_id", "created_at", "created_by_id", "description", "due_date", "folder_id_id", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "task_status_id", "title") VALUES (NEW."assignee_id", NEW."case_id_id", NEW."created_at", NEW."created_by_id", NEW."description", NEW."due_date", NEW."folder_id_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."task_status_id", NEW."title"); RETURN NULL;', hash='8ec839de0ba611ebbd3309e0bdf085538437dd8b', operation='UPDATE', pgid='pgtrigger_snapshot_update_76b66', table='activities_task', when='AFTER')),
        ),
    ]