from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import *


# Register your models here.

class payments_inline(admin.StackedInline):
    model = Payment
    extra = 0
    # fields = ('amount',)
    # readonly_fields = fields

class ContractAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'company', 'is_deleted')
    fields = ('name', 'description', 'company', 'out_side_iraq', 'total_amount', 'start_time', 'end_time',
              'first_party', 'second_party', 'third_party', 'auto_renewal', 'penal_clause', 'paths',
              'ImportantDevelopment', 'comments', 'assignee', 'shared_with', 'is_deleted', 'created_by', 'created_at',
              'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')
    inlines = [payments_inline,]



class PaymentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('amount', 'date', 'duration', 'contract', 'is_deleted')
    fields = ('amount', 'date', 'duration', 'contract', 'is_deleted', 'created_by', 'created_at',
              'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


class ReminderAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('payment', 'reminder_date', 'is_sent', 'created_by', 'created_at')
    fields = list_display
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')

class DurationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'type', 'no_of_days', 'reminder_days', 'is_recurring', 'is_deleted')
    fields = ('type', 'no_of_days', 'reminder_days', 'is_recurring', 'is_deleted', 'created_by', 'created_at', 'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


class TypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'name', 'is_deleted')
    fields = ('name', 'is_deleted', 'created_by', 'created_at', 'modified_by', 'modified_at')
    readonly_fields = ('created_by', 'created_at', 'modified_by', 'modified_at')


admin.site.register(Contract, ContractAdmin)
# admin.site.register(Payment)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Reminder, ReminderAdmin)
admin.site.register(Duration, DurationAdmin)
admin.site.register(Type, TypeAdmin)
