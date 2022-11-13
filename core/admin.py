from django.contrib import admin
from .models import comments,priorities,replies,court,contracts,documents
from import_export.admin import ImportExportModelAdmin


class commentsAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'comment','case_id','task_id','hearing_id','is_deleted')

class courtAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'name')

class repliesAdmin(admin.ModelAdmin):
    list_display = ('id', 'reply','is_deleted')

class prioritiesAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'priority')

class contractsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','attachment','is_deleted')

class documentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','attachment','is_deleted')

admin.site.register(priorities, prioritiesAdmin)
admin.site.register(contracts, contractsAdmin)
admin.site.register(documents, documentsAdmin)
admin.site.register(court, courtAdmin)
admin.site.register(comments, commentsAdmin)
admin.site.register(replies, repliesAdmin)