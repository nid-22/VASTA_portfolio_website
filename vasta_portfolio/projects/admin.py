import os
import cloudinary
import cloudinary.uploader
from django.contrib import admin
from django import forms
from django.conf import settings
from django.utils.html import format_html

from .models import Typology, Location, Project, ProjectImage, SubType


class OptionalFileField(forms.FileField):
    """Treats empty-filename browser submissions as "no file" to avoid
    the 'No file was submitted' validation error some browsers trigger."""

    def to_python(self, data):
        if data in self.empty_values:
            return None
        if hasattr(data, 'name') and not data.name:
            return None
        return super().to_python(data)


cloudinary_conf = getattr(settings, 'CLOUDINARY_STORAGE', {})
if cloudinary_conf.get('CLOUD_NAME') or os.environ.get('CLOUDINARY_CLOUD_NAME'):
    cloudinary.config(
        cloud_name=cloudinary_conf.get('CLOUD_NAME') or os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=cloudinary_conf.get('API_KEY') or os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=cloudinary_conf.get('API_SECRET') or os.environ.get('CLOUDINARY_API_SECRET'),
    )


class ProjectImageInlineForm(forms.ModelForm):
    image_file = OptionalFileField(
        required=False,
        label='Upload Image',
        help_text='Upload a new image (will be uploaded to Cloudinary)',
    )

    class Meta:
        model = ProjectImage
        fields = ('image', 'image_file')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['image'].widget.attrs['placeholder'] = 'Cloudinary URL (auto-filled on upload)'
        self.fields['image'].help_text = 'Current image URL (or paste a URL directly)'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('image_file'):
            uploaded_file = self.cleaned_data['image_file']
            try:
                result = cloudinary.uploader.upload(
                    uploaded_file,
                    folder='vast_projects',
                    resource_type='image',
                )
                instance.image = result['secure_url']
            except Exception as e:
                self.add_error(None, f'Image upload failed: {e}')
        if commit:
            instance.save()
        return instance


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    form = ProjectImageInlineForm
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_file', 'image_preview')

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="max-height:80px;"/>', obj.image)
        return ""

    image_preview.short_description = 'Preview'


class ProjectImageUploadForm(forms.ModelForm):
    cover_image_file = OptionalFileField(
        widget=forms.FileInput(),
        required=False,
        label='Upload cover image',
        help_text='Upload a new cover image (will be uploaded to Cloudinary)',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].required = False
        self.fields['cover_image'].help_text = 'Current cover image URL (or paste a URL directly)'

    class Meta:
        model = Project
        fields = '__all__'


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectImageUploadForm
    inlines = [ProjectImageInline]
    list_display = ('heading', 'typology', 'location', 'project_year', 'order_to_display_id', 'is_active', 'updated')
    search_fields = ('heading', 'short_description', 'long_description', 'client')
    list_filter = ('typology', 'location', 'project_year', 'is_active')
    list_editable = ('order_to_display_id',)
    ordering = ('order_to_display_id',)

    def save_model(self, request, obj, form, change):
        cover_file = form.cleaned_data.get('cover_image_file')
        if cover_file:
            try:
                result = cloudinary.uploader.upload(
                    cover_file,
                    folder='vast_projects',
                    resource_type='image',
                )
                obj.cover_image = result['secure_url']
            except Exception as e:
                self.message_user(request, f'Cover image upload failed: {e}', level='error')

        super().save_model(request, obj, form, change)


class TypologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'updated')
    search_fields = ('name',)


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'updated')
    search_fields = ('name',)
    list_filter = ('is_active',)


class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'updated', 'is_active')
    search_fields = ('project__heading',)
    list_filter = ('project', 'is_active')


class SubTypeAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(Typology, TypologyAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)
admin.site.register(SubType, SubTypeAdmin)
