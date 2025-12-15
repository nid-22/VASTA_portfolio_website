from django.contrib import admin
from django import forms
from django.utils.html import format_html

from .models import Typology, Location, Project, ProjectImage, SubType

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
class ProjectImageUploadForm(forms.ModelForm):
    """Custom ModelForm for ProjectAdmin that exposes a multiple file input
    named `process_images_upload` to allow uploading many files at once.
    """
    process_images_upload = forms.FileField(
        widget=forms.FileInput(),
        required=False,
        label='Upload process images',
        help_text='Select multiple images to upload and attach to this project.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enable multiple file selection on the widget at runtime to avoid
        # Django raising at import time when multiple is set on widget attrs.
        widget = self.fields['process_images_upload'].widget
        try:
            widget.allow_multiple_selected = True
        except Exception:
            pass
        widget.attrs.update({'multiple': True})

    class Meta:
        model = Project
        fields = '__all__'


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_preview',)

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:80px;"/>', obj.image.url)
        return ""

    image_preview.short_description = 'Preview'


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectImageUploadForm
    inlines = [ProjectImageInline]
    list_display = ('heading', 'typology', 'location', 'project_year', 'order_to_display_id', 'grid_shape', 'is_active', 'updated')
    search_fields = ('heading', 'short_description', 'long_description', 'client')
    list_filter = ('typology', 'location', 'project_year', 'grid_shape', 'is_active')
    list_editable = ('order_to_display_id',)
    ordering = ('order_to_display_id',)

    def save_model(self, request, obj, form, change):
        # Save the Project first so we have a PK to attach images to
        super().save_model(request, obj, form, change)

        # Handle multiple uploaded files from the custom file input
        files = request.FILES.getlist('process_images_upload')
        for f in files:
            ProjectImage.objects.create(project=obj, image=f)

# Optional: Customize admin interface for ProjectImage
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'updated', 'is_active')
    search_fields = ('project__heading',)
    list_filter = ('project', 'is_active')

class SubTypeAdmin(admin.ModelAdmin):
    list_display = ['name']

# Register your models here
admin.site.register(Typology, TypologyAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)
admin.site.register(SubType, SubTypeAdmin)
