# Generated by Django 4.1.3 on 2023-01-29 11:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import pgtrigger.compiler
import pgtrigger.migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0009_remove_documents_snapshot_insert_and_more'),
    ]

    operations = [
        pgtrigger.migrations.RemoveTrigger(
            model_name='path',
            name='snapshot_insert',
        ),
        pgtrigger.migrations.RemoveTrigger(
            model_name='path',
            name='snapshot_update',
        ),
        migrations.AddField(
            model_name='path',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='path',
            name='created_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_createdby', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='path',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='path',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='path',
            name='modified_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_modifiedby', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathevent',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pathevent',
            name='created_by',
            field=models.ForeignKey(blank=True, db_constraint=False, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='pathevent',
            name='is_deleted',
            field=models.BooleanField(default=False, verbose_name='Is Deleted'),
        ),
        migrations.AddField(
            model_name='pathevent',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='pathevent',
            name='modified_by',
            field=models.ForeignKey(blank=True, db_constraint=False, editable=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', related_query_name='+', to=settings.AUTH_USER_MODEL),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='path',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_insert', sql=pgtrigger.compiler.UpsertTriggerSql(func='INSERT INTO "core_pathevent" ("created_at", "created_by_id", "id", "is_deleted", "level", "lft", "modified_at", "modified_by_id", "name", "parent_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "rght", "tree_id") VALUES (NEW."created_at", NEW."created_by_id", NEW."id", NEW."is_deleted", NEW."level", NEW."lft", NEW."modified_at", NEW."modified_by_id", NEW."name", NEW."parent_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."rght", NEW."tree_id"); RETURN NULL;', hash='f8ba15231845f9635b78cd9862aa9c51a7b274f4', operation='INSERT', pgid='pgtrigger_snapshot_insert_5eab7', table='core_path', when='AFTER')),
        ),
        pgtrigger.migrations.AddTrigger(
            model_name='path',
            trigger=pgtrigger.compiler.Trigger(name='snapshot_update', sql=pgtrigger.compiler.UpsertTriggerSql(condition='WHEN (OLD.* IS DISTINCT FROM NEW.*)', func='INSERT INTO "core_pathevent" ("created_at", "created_by_id", "id", "is_deleted", "level", "lft", "modified_at", "modified_by_id", "name", "parent_id", "pgh_context_id", "pgh_created_at", "pgh_label", "pgh_obj_id", "rght", "tree_id") VALUES (NEW."created_at", NEW."created_by_id", NEW."id", NEW."is_deleted", NEW."level", NEW."lft", NEW."modified_at", NEW."modified_by_id", NEW."name", NEW."parent_id", _pgh_attach_context(), NOW(), \'snapshot\', NEW."id", NEW."rght", NEW."tree_id"); RETURN NULL;', hash='a02c388237055655afca2285af0cf7a4b019a60d', operation='UPDATE', pgid='pgtrigger_snapshot_update_56fb9', table='core_path', when='AFTER')),
        ),
    ]
