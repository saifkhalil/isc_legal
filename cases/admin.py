from django.contrib import admin
from .models import *
from parler.admin import TranslatableAdmin


# Register your models here.
class LitigationCasesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','description','practice_area')

    def save(self, *args, **kwargs):
        if self.cid is None:
            self.cid = 'C-' + str(self.id)
        return super(LitigationCases, self).save(*args, **kwargs)

# class practice_areaAdmin(admin.ModelAdmin):
#     list_display = ('id', 'name')

class stagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    
class prioritiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'priority')

class case_statusAdmin(admin.ModelAdmin):
    list_display = ('id', 'status')
    
class client_positionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class client_typeAdmin(admin.ModelAdmin):
    list_display = ('id', 'type')

class opponent_positionAdmin(admin.ModelAdmin):
    list_display = ('id', 'position')

class CompaniesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class personsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class company_legal_typeAdmin(admin.ModelAdmin):
    list_display = ('id', 'legal_type')

class companies_groupAdmin(admin.ModelAdmin):
    list_display = ('id', 'group')

class companies_sub_categoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'sub_category')

class companies_categoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category')

class companies_addressAdmin(admin.ModelAdmin):
    list_display = ('id', 'company','address','state','zip','street_name','building_number','district','mobile','country')


admin.site.register(LitigationCases, LitigationCasesAdmin)
admin.site.register(practice_area, TranslatableAdmin)
admin.site.register(stages, stagesAdmin)
admin.site.register(client_position, client_positionAdmin)
admin.site.register(client_type, client_typeAdmin)
admin.site.register(opponent_position, opponent_positionAdmin)
admin.site.register(company, CompaniesAdmin)
admin.site.register(persons, personsAdmin)
admin.site.register(case_status, case_statusAdmin)
admin.site.register(company_legal_type, company_legal_typeAdmin)
admin.site.register(companies_group, companies_groupAdmin)
admin.site.register(companies_sub_category, companies_sub_categoryAdmin)
admin.site.register(companies_category, companies_categoryAdmin)
admin.site.register(companies_address, companies_addressAdmin)
