from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTModelAdmin

from .models import comments, priorities, replies, court, contracts, documents, Status, Path, Notification


class commentsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('comment', 'case_id',
                    'task_id', 'hearing_id', 'is_deleted','created_by','created_at')
    fields = list_display
    readonly_fields = ('created_at','created_by')
class courtAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')


class repliesAdmin(admin.ModelAdmin):
    list_display = ('id', 'reply', 'is_deleted','created_by','created_at')


class prioritiesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'priority', 'color', 'icon',)


class contractsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'attachment', 'is_deleted')


class documentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'attachment', 'is_deleted')


class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'status','color', 'icon', 'is_completed', 'is_done')


class NotificationsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        #'model',
        #'obj',
        'content_type',
        'object_id',
        'object_name',
        'action',
        'is_read',
        'user',
        'role',
        'action_by',
        'action_at'
    )
    fields = (
        #'model',
        #'obj',
        'action',
        'content_type',
        'object_id',
        'user',
        'role',
        'is_read',
        'action_by'
    )


class PathModelAdmin(ImportExportModelAdmin, MPTTModelAdmin):
    # specify pixel amount for this ModelAdmin only:
    fields = (
        'name', 'parent', 'documents', 'is_deleted', 'case_id', 'folder_id', 'admin_id', 'notation_id', 'created_by'
              )
    list_display = (
        'id',
        'name',
        'folder_id',
        'case_id',
        'notation_id',
        'created_by',
        'created_at'
    )
    mptt_level_indent = 20

admin.site.register(Notification, NotificationsAdmin)
admin.site.register(Path, PathModelAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(priorities, prioritiesAdmin)
admin.site.register(contracts, contractsAdmin)
admin.site.register(documents, documentsAdmin)
admin.site.register(court, courtAdmin)
admin.site.register(comments, commentsAdmin)
admin.site.register(replies, repliesAdmin)
