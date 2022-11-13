from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import User,Department
from django.utils import timezone
# Register your models here.


class UserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'email', 'firstname', 'lastname','Manager', 'is_verified', 'is_blocked','created_by','created_at','modified_by','modified_at')
    # fields = ('email', 'firstname', 'lastname','Manager','is_manager','is_verified', 'is_blocked','created_by','created_at','modified_by','modified_at')
    readonly_fields = ('created_by','created_at','modified_by','modified_at')
    list_filter = ( 'is_verified', 'is_blocked','Manager',)
    search_fields = ('email', 'firstname', 'lastname')

    def save_model(self, request, obj, form, change):
        if change:
            obj.modified_by = request.user
            obj.modified_at = timezone.now
        else:
            obj.created_by = request.user
            obj.created_at = timezone.now
        obj.save()

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','Description')

admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)