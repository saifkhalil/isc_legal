from django.contrib import admin
from .models import *
# Register your models here.


# class task_typeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'type')

# class event_typeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'type')

# class hearing_typeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'type')

class taskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','description','assignee','due_date','is_deleted')

class hearingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','hearing_date','case_id','is_deleted')

# class eventAdmin(admin.ModelAdmin):
#     list_display = ('id','eid', 'event_type','created_by','from_date','to_date')
#     readonly_fields = ['eid']

# admin.site.register(task_type, task_typeAdmin)
admin.site.register(task, taskAdmin)
admin.site.register(hearing, hearingAdmin)
# admin.site.register(hearing_type, hearing_typeAdmin)
# admin.site.register(event_type, event_typeAdmin)
# admin.site.register(event, eventAdmin)