from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.CanvasType)
admin.site.register(models.Priority)
admin.site.register(models.Canvas)
admin.site.register(models.CanvasTask)
admin.site.register(models.CanvasMembers)
admin.site.register(models.CanvasNotes) 
