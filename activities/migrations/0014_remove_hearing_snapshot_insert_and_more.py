# Generated by Django 4.1.3 on 2023-01-11 07:33

from django.db import migrations, models
import django.db.models.deletion
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_status"),
        ("activities", "0013_hearingevent_taskevent_hearing_snapshot_insert_and_more"),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name="hearing",
            name="snapshot_insert",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="hearing",
            name="snapshot_update",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="task",
            name="snapshot_insert",
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name="task",
            name="snapshot_update",
        ),
        migrations.AddField(
            model_name="hearing",
            name="hearing_status",
            field=models.ForeignKey(
                default="",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_hearing_status",
                to="core.status",
                verbose_name="Hearing Status",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="hearingevent",
            name="hearing_status",
            field=models.ForeignKey(
                db_constraint=False,
                default="",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="core.status",
                verbose_name="Hearing Status",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="task",
            name="task_status",
            field=models.ForeignKey(
                default="",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s_task_status",
                to="core.status",
                verbose_name="Task Status",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="taskevent",
            name="task_status",
            field=models.ForeignKey(
                db_constraint=False,
                default="",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                related_query_name="+",
                to="core.status",
                verbose_name="Task Status",
            ),
            preserve_default=False,
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="hearing",
            trigger=pgtrigger.compiler.Trigger(
                name="snapshot_insert",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;',
                    hash="db406fd94ca78f7d6ea3ae5f327fb6d7ef8297e9",
                    operation="INSERT",
                    pgid="pgtrigger_snapshot_insert_28885",
                    table="activities_hearing",
                    when="AFTER",
                ),
            ),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="hearing",
            trigger=pgtrigger.compiler.Trigger(
                name="snapshot_update",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    condition="WHEN (OLD.* IS DISTINCT FROM NEW.*)",
                    func='INSERT INTO "activities_hearingevent" ("assignee_id", "case_id", "comments_by_lawyer", "court_id", "created_at", "created_by_id", "hearing_date", "hearing_status_id", "id", "is_deleted", "modified_at", "modified_by_id", "name", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id") VALUES (NEW."assignee_id", NEW."case_id", NEW."comments_by_lawyer", NEW."court_id", NEW."created_at", NEW."created_by_id", NEW."hearing_date", NEW."hearing_status_id", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", NEW."name", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id"); RETURN NULL;',
                    hash="14777ad252706698940e967df994893aae95de0f",
                    operation="UPDATE",
                    pgid="pgtrigger_snapshot_update_94291",
                    table="activities_hearing",
                    when="AFTER",
                ),
            ),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="task",
            trigger=pgtrigger.compiler.Trigger(
                name="snapshot_insert",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    func='INSERT INTO "activities_taskevent" ("assignee_id", "case_id", "created_at", "created_by_id", "description", "due_date", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "task_status_id", "title") VALUES (NEW."assignee_id", NEW."case_id", NEW."created_at", NEW."created_by_id", NEW."description", NEW."due_date", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."task_status_id", NEW."title"); RETURN NULL;',
                    hash="f65ad345a95acc85d28462be49c11bba6586ce88",
                    operation="INSERT",
                    pgid="pgtrigger_snapshot_insert_0cb53",
                    table="activities_task",
                    when="AFTER",
                ),
            ),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name="task",
            trigger=pgtrigger.compiler.Trigger(
                name="snapshot_update",
                sql=pgtrigger.compiler.UpsertTriggerSql(
                    condition="WHEN (OLD.* IS DISTINCT FROM NEW.*)",
                    func='INSERT INTO "activities_taskevent" ("assignee_id", "case_id", "created_at", "created_by_id", "description", "due_date", "id", "is_deleted", "modified_at", "modified_by_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "task_status_id", "title") VALUES (NEW."assignee_id", NEW."case_id", NEW."created_at", NEW."created_by_id", NEW."description", NEW."due_date", NEW."id", NEW."is_deleted", NEW."modified_at", NEW."modified_by_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."task_status_id", NEW."title"); RETURN NULL;',
                    hash="9b16459bef26f4f9b7fdff1229b1aa8ce3e75e67",
                    operation="UPDATE",
                    pgid="pgtrigger_snapshot_update_76b66",
                    table="activities_task",
                    when="AFTER",
                ),
            ),
        ),
    ]
