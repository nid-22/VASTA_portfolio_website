from django.contrib import admin
from .models import Typology, Location, Project, ProcessImages, SubType

# Optional: Customize admin interface for Typology
class TypologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'updated') # Customize as needed
    search_fields = ('name',)

# Optional: Customize admin interface for Location
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'updated')
    search_fields = ('name',)
    list_filter = ('is_active',)

# Optional: Customize admin interface for Project
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('heading', 'typology', 'location', 'project_year', 'is_active', 'updated')
    search_fields = ('heading', 'description', 'client')
    list_filter = ('typology', 'location', 'project_year', 'is_active')

# Optional: Customize admin interface for ProcessImages
class ProcessImagesAdmin(admin.ModelAdmin):
    list_display = ('project', 'updated', 'is_active')
    search_fields = ('project__heading',)
    list_filter = ('project', 'is_active')

class SubTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

# Register your models here
admin.site.register(Typology, TypologyAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProcessImages, ProcessImagesAdmin)
admin.site.register(SubType, SubTypeAdmin)
