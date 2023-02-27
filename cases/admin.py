from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *


class LitigationCasesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_deleted')
    fields = ('name', 'description', 'case_category', 'judge', 'tasks', 'comments', 'detective', 'ImportantDevelopment',
              'case_type', 'case_status', 'court', 'documents', 'client_position', 'opponent_position', 'assignee',
              'shared_with', 'priority', 'end_time', 'start_time', 'is_deleted', 'created_by', 'created_at',
              'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


class FoldersAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_deleted')
    fields = (
        'name', 'description', 'folder_category', 'judge', 'tasks', 'comments', 'detective', 'ImportantDevelopment',
        'folder_type', 'court', 'documents', 'client_position', 'opponent_position', 'assignee', 'shared_with',
        'priority',
        'end_time', 'start_time', 'is_deleted', 'created_by', 'created_at', 'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


class LitigationCasesEventAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id',)


class case_typeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'type')


class ImportantDevelopmentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'title')


class stagesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')


class prioritiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'priority')


class case_statusAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'status')


class client_positionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')


class opponent_positionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'position')


class case_typeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'type')


admin.site.register(LitigationCases, LitigationCasesAdmin)
admin.site.register(Folder, FoldersAdmin)
admin.site.register(ImportantDevelopment, ImportantDevelopmentAdmin)
admin.site.register(stages, stagesAdmin)
admin.site.register(case_type, case_typeAdmin)
admin.site.register(client_position, client_positionAdmin)
admin.site.register(opponent_position, opponent_positionAdmin)
