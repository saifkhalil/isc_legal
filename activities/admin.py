from django.contrib import admin

from .models import *
class taskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'assignee', 'due_date', 'task_status', 'is_deleted')


class hearingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hearing_date', 'case_id', 'hearing_status', 'is_deleted')


admin.site.register(task, taskAdmin)
admin.site.register(hearing, hearingAdmin)
