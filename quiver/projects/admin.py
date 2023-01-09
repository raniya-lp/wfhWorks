from django.contrib import admin
from . import models
admin.site.register(models.Projects)
admin.site.register(models.ProjectsOrganizationMapping)
admin.site.register(models.RoadMaps)
admin.site.register(models.Collaborator)
admin.site.register(models.RoadMapFeatures)
# Register your models here.
