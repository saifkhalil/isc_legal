from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTModelAdmin

from .models import comments, priorities, replies, court, contracts, documents, Status, Path


class commentsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'comment', 'case_id', 'task_id', 'hearing_id', 'is_deleted')


class courtAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')


class repliesAdmin(admin.ModelAdmin):
    list_display = ('id', 'reply', 'is_deleted')


class prioritiesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'priority')


class contractsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'attachment', 'is_deleted')


class documentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'attachment', 'is_deleted')


class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'status')


class PathModelAdmin(MPTTModelAdmin):
    # specify pixel amount for this ModelAdmin only:
    mptt_level_indent = 20


admin.site.register(Path, PathModelAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(priorities, prioritiesAdmin)
admin.site.register(contracts, contractsAdmin)
admin.site.register(documents, documentsAdmin)
admin.site.register(court, courtAdmin)
admin.site.register(comments, commentsAdmin)
admin.site.register(replies, repliesAdmin)
