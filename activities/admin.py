from django.contrib import admin
from .models import *
# Register your models here.


class task_typeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')

class event_typeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')

class hearing_typeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')

class taskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','task_type','description','assigned_to','requested_by','priority','due_date')

class hearingAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','hearing_type','hearing_date','time_spent','summary_by_lawyer')

class eventAdmin(admin.ModelAdmin):
    list_display = ('id','eid', 'event_type','created_by','from_date','to_date')
    readonly_fields = ['eid']

admin.site.register(task_type, task_typeAdmin)
admin.site.register(task, taskAdmin)
admin.site.register(hearing, hearingAdmin)
admin.site.register(hearing_type, hearing_typeAdmin)
admin.site.register(event_type, event_typeAdmin)
admin.site.register(event, eventAdmin)