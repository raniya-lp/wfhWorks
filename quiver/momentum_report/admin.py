from django.contrib import admin
from . models import *
# Register your models here.
class taskAdminCheck(admin.ModelAdmin):
    list_display=['workspacename','enddate','updated_at']
    ordering = ['updated_at']

admin.site.register(Task,taskAdminCheck)
admin.site.register(ProjectLogo)
admin.site.register(Report_Pdf)
admin.site.register(default_logo)
admin.site.register(Report)
admin.site.register(ProjectFromWorkzone)
admin.site.register(TaskNotification)

admin.site.register(ReportShare)