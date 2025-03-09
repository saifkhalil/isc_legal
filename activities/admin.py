from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *


class taskAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'title', 'description',  'due_date', 'assign_date', 'task_status', 'is_deleted','modified_by')


class hearingAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'hearing_date', 'case_id', 'hearing_status', 'remind_me', 'is_deleted')


admin.site.register(task, taskAdmin)
admin.site.register(hearing, hearingAdmin)
