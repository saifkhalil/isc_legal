from django.contrib import admin
from .models import comments,priorities,replies

class commentsAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment')

class repliesAdmin(admin.ModelAdmin):
    list_display = ('id', 'reply')

class prioritiesAdmin(admin.ModelAdmin):
    list_display = ('id', 'priority')

admin.site.register(priorities, prioritiesAdmin)
admin.site.register(comments, commentsAdmin)
admin.site.register(replies, repliesAdmin)