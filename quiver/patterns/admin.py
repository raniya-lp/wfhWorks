from django.contrib import admin
from . import models
# Register your models here.
admin.site.register(models.Pattern)
admin.site.register(models.PatternSection)
admin.site.register(models.PatternSubSection)
admin.site.register(models.PatternSectionCollection)
admin.site.register(models.PatternFont)