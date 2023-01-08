from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin

# Register your models here.




class LitigationCasesAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'name','description','is_deleted')
    fields = ( 'name','description','case_category','judge','comments','detective','case_type','court','documents','client_position','opponent_position','assignee','shared_with','priority','end_time','start_time','is_deleted','created_by','created_at','modified_by','modified_at')
    readonly_fields = ('created_by','created_at','modified_by','modified_at')

    def save(self, *args, **kwargs):
        if self.cid is None:
            self.cid = 'C-' + str(self.id)
        return super(LitigationCases, self).save(*args, **kwargs)

class FoldersAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'name','description','is_deleted')
    fields = ( 'name','description','folder_category','judge','comments','detective','folder_type','court','documents','client_position','opponent_position','assignee','shared_with','priority','end_time','start_time','is_deleted','created_by','created_at','modified_by','modified_at')
    readonly_fields = ('created_by','created_at','modified_by','modified_at')

    def save(self, *args, **kwargs):
        if self.cid is None:
            self.cid = 'F-' + str(self.id)
        return super(Folder, self).save(*args, **kwargs)

class LitigationCasesEventAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id',)



class case_typeAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'type')

class stagesAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'name')
    
class prioritiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'priority')

class case_statusAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'status')
    
class client_positionAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'name')

# class client_typeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'type')

class opponent_positionAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'position')


class case_typeAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('id', 'type')

# class CompaniesAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')

# class personsAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')

# class company_legal_typeAdmin(admin.ModelAdmin):
#     list_display = ('id', 'legal_type')

# class companies_groupAdmin(admin.ModelAdmin):
#     list_display = ('id', 'group')

# class companies_sub_categoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'sub_category')

# class companies_categoryAdmin(admin.ModelAdmin):
#     list_display = ('id', 'category')

# class companies_addressAdmin(admin.ModelAdmin):
#     list_display = ('id', 'company','address','state','zip','street_name','building_number','district','mobile','country')


admin.site.register(LitigationCases, LitigationCasesAdmin)
admin.site.register(Folder, FoldersAdmin)
admin.site.register(LitigationCasesEvent, LitigationCasesEventAdmin)
admin.site.register(stages, stagesAdmin)
admin.site.register(case_type, case_typeAdmin)
admin.site.register(client_position, client_positionAdmin)
# admin.site.register(client_type, client_typeAdmin)
admin.site.register(opponent_position, opponent_positionAdmin)
# admin.site.register(company, CompaniesAdmin)
# admin.site.register(persons, personsAdmin)
# admin.site.register(case_status, case_statusAdmin)
# admin.site.register(company_legal_type, company_legal_typeAdmin)
# admin.site.register(companies_group, companies_groupAdmin)
# admin.site.register(companies_sub_category, companies_sub_categoryAdmin)
# admin.site.register(companies_category, companies_categoryAdmin)
# admin.site.register(companies_address, companies_addressAdmin)
