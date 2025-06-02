from django.contrib import admin,messages
from import_export.admin import ImportExportModelAdmin
from mptt.admin import MPTTModelAdmin
from django.utils.html import format_html

from .models import comments, priorities, replies, court, contracts, documents, Status, Path, Notification, \
    documentImage, documentPage

def process_selected_documents(modeladmin, request, queryset):
    for document in queryset:
        try:
            document.process_document()
            modeladmin.message_user(
                request,
                f"Processed: {document.name}",
                level=messages.SUCCESS
            )
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Failed to process {document.name}: {e}",
                level=messages.ERROR
            )

process_selected_documents.short_description = "Re-process selected documents"

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




class DocumentImageInline(admin.TabularInline):
    model = documentImage
    extra = 0
    readonly_fields = ['image',]
    can_delete = False

class DocumentPageInline(admin.TabularInline):
    model = documentPage
    extra = 0
    readonly_fields = ['image', 'page_number']
    can_delete = False


class documentsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'attachment', 'is_deleted']
    search_fields = ['name','extracted_text']
    list_filter = ['is_deleted', 'created_at']
    inlines = [DocumentImageInline, DocumentPageInline]
    actions = [process_selected_documents]

    def preview_link(self, obj):
        urls = obj.get_preview_image()
        if urls:
            return format_html('<a href="{}" target="_blank">Preview First Page</a>', urls[0])
        return "-"
    preview_link.short_description = "Preview"
    list_display += ['preview_link']


class documentImageAdmin(admin.ModelAdmin):
    list_display = ['document', 'image']
    readonly_fields = ['image']

class documentPageAdmin(admin.ModelAdmin):
    list_display = ['image', 'page_number']
    readonly_fields = ['text']

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
admin.site.register(documentImage, documentImageAdmin)
admin.site.register(documentPage, documentPageAdmin)
admin.site.register(court, courtAdmin)
admin.site.register(comments, commentsAdmin)
admin.site.register(replies, repliesAdmin)
