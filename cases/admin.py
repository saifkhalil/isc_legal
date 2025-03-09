from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import *


class LitigationCasesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_deleted', 'assignee')
    fields = ('name', 'description', 'case_category', 'judge', 'tasks', 'hearing', 'comments', 'detective', 'ImportantDevelopment',
              'case_type', 'case_status', 'Stage', 'characteristic', 'court', 'documents', 'paths', 'client_position', 'opponent_position', 'assignee', 'case_close_status', 'case_close_comment',
              'shared_with', 'priority', 'end_time', 'start_time', 'is_deleted', 'created_by', 'created_at',
              'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')
    list_filter = ['assignee', 'Stage', 'case_status']

class FoldersAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_deleted')
    fields = (
        'name', 'description', 'folder_category', 'judge', 'tasks', 'comments', 'detective', 'ImportantDevelopment',
        'folder_type', 'court', 'documents', 'client_position', 'opponent_position', 'assignee', 'shared_with',
        'priority',
        'end_time', 'start_time', 'is_deleted', 'created_by', 'created_at', 'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


class AdministrativeInvestigationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'subject', 'admin_order_number', 'is_deleted')
    fields = ('subject', 'admin_order_number', 'chairman', 'members', 'start_time', 'end_time',
              'shared_with', 'assignee', 'ImportantDevelopment', 'paths',
               'is_deleted', 'created_by', 'created_at', 'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')

class NotationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'subject', 'description', 'is_deleted', 'created_by')
    fields = ('subject', 'description', 'assignee', 'shared_with', 'reference_number', 'reference_date',
              'notation_date', 'requester', 'court', 'judge', 'detective', 'authorized_number', 'ImportantDevelopment',
              'comments', 'priority', 'end_time', 'start_time', 'is_deleted', 'created_by', 'created_at',
              'modified_by', 'modified_at'
              )
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')
    list_filter = ("created_by", )

class LitigationCasesEventAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id',)


class case_typeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'type', 'is_deleted')


class ImportantDevelopmentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'title')


class stagesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'is_deleted')



class prioritiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'priority')


class client_positionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')

class characteristicAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name')


class opponent_positionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'position')


class case_typeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'type')


admin.site.register(LitigationCases, LitigationCasesAdmin)
admin.site.register(AdministrativeInvestigation, AdministrativeInvestigationAdmin)
admin.site.register(Notation, NotationAdmin)
admin.site.register(Folder, FoldersAdmin)
admin.site.register(ImportantDevelopment, ImportantDevelopmentAdmin)
admin.site.register(stages, stagesAdmin)
admin.site.register(characteristic, characteristicAdmin)
admin.site.register(case_type, case_typeAdmin)
admin.site.register(client_position, client_positionAdmin)
admin.site.register(opponent_position, opponent_positionAdmin)
