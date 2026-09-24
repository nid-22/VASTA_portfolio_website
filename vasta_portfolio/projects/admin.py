import os
from urllib.parse import quote

import cloudinary
import cloudinary.uploader
from django.contrib import admin
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from PIL import Image, UnidentifiedImageError

from .models import (
    CareerSubmission,
    ContactSubmission,
    DailyAnalyticsMetric,
    Discipline,
    Location,
    Project,
    ProjectImage,
    SubType,
    Typology,
)


MAX_CAROUSEL_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB
DESKTOP_CAROUSEL_MIN_SIZE = (1920, 1080)
MOBILE_CAROUSEL_MIN_SIZE = (1080, 1350)


def validate_carousel_image(uploaded_file, *, minimum_size, orientation, label):
    """Validate carousel uploads before sending them to Cloudinary."""
    if not uploaded_file:
        return uploaded_file

    if uploaded_file.size > MAX_CAROUSEL_IMAGE_SIZE:
        raise ValidationError(f'{label} must be 20 MB or smaller.')

    content_type = getattr(uploaded_file, 'content_type', '')
    if content_type and not content_type.startswith('image/'):
        raise ValidationError(f'{label} must be an image file.')

    try:
        image = Image.open(uploaded_file)
        width, height = image.size
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(f'{label} could not be read as an image.')
    finally:
        uploaded_file.seek(0)

    minimum_width, minimum_height = minimum_size
    if width < minimum_width or height < minimum_height:
        raise ValidationError(
            f'{label} must be at least {minimum_width} × {minimum_height} px. '
            f'This file is {width} × {height} px.'
        )

    if orientation == 'landscape' and width <= height:
        raise ValidationError(f'{label} must be a landscape image (wider than it is tall).')
    if orientation == 'portrait' and height <= width:
        raise ValidationError(f'{label} must be a portrait image (taller than it is wide).')

    return uploaded_file


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
    carousel_desktop_image_file = OptionalFileField(
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        required=False,
        label='Upload desktop carousel image',
        help_text='Landscape, at least 1920 × 1080 px. Maximum file size: 20 MB.',
    )
    carousel_mobile_image_file = OptionalFileField(
        widget=forms.FileInput(attrs={'accept': 'image/*'}),
        required=False,
        label='Upload phone carousel image',
        help_text='Portrait, at least 1080 × 1350 px. Maximum file size: 20 MB.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_image'].required = False
        self.fields['cover_image'].help_text = 'Current cover image URL (or paste a URL directly)'
        self.fields['carousel_desktop_image'].required = False
        self.fields['carousel_desktop_image'].help_text = (
            'Current desktop carousel image URL. If empty, the cover image is used.'
        )
        self.fields['carousel_mobile_image'].required = False
        self.fields['carousel_mobile_image'].help_text = (
            'Current phone carousel image URL. If empty, the desktop carousel image '
            'or cover image is used.'
        )

    def clean_carousel_desktop_image_file(self):
        return validate_carousel_image(
            self.cleaned_data.get('carousel_desktop_image_file'),
            minimum_size=DESKTOP_CAROUSEL_MIN_SIZE,
            orientation='landscape',
            label='Desktop carousel image',
        )

    def clean_carousel_mobile_image_file(self):
        return validate_carousel_image(
            self.cleaned_data.get('carousel_mobile_image_file'),
            minimum_size=MOBILE_CAROUSEL_MIN_SIZE,
            orientation='portrait',
            label='Phone carousel image',
        )

    class Meta:
        model = Project
        fields = '__all__'


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectImageUploadForm
    inlines = [ProjectImageInline]
    list_display = ('heading', 'category', 'discipline_list', 'location', 'project_year', 'status', 'order_to_display_id', 'is_active', 'updated')
    search_fields = ('heading', 'short_description', 'long_description', 'client')
    list_filter = ('disciplines', 'category', 'status', 'location', 'project_year', 'is_active')
    list_editable = ('order_to_display_id',)
    ordering = ('order_to_display_id',)
    readonly_fields = ('carousel_desktop_preview', 'carousel_mobile_preview')
    fieldsets = (
        ('Project details', {
            'fields': (
                'heading', 'slug', 'short_description', 'long_description',
                'project_year', 'status', 'category', 'disciplines', 'sub_type', 'size',
                'content', 'location', 'client',
            ),
        }),
        ('Project grid image', {
            'fields': ('cover_image', 'cover_image_file'),
        }),
        ('Homepage carousel', {
            'description': (
                'Upload separate high-resolution images for the homepage carousel. '
                'Desktop falls back to the project cover; phone falls back to the '
                'desktop carousel image and then the cover.'
            ),
            'fields': (
                'carousel_desktop_image', 'carousel_desktop_image_file',
                'carousel_desktop_preview', 'carousel_mobile_image',
                'carousel_mobile_image_file', 'carousel_mobile_preview',
            ),
        }),
        ('Display and availability', {
            'fields': ('order_to_display_id', 'is_active', 'is_deleted'),
        }),
    )

    @admin.display(description='Disciplines')
    def discipline_list(self, obj):
        return ' · '.join(discipline.name for discipline in obj.disciplines.all()) or '—'

    @admin.display(description='Desktop preview')
    def carousel_desktop_preview(self, obj):
        if obj and obj.carousel_desktop_image:
            return format_html(
                '<img src="{}" alt="" style="max-width:420px; max-height:180px; '
                'object-fit:cover; border-radius:3px;" />',
                obj.carousel_desktop_image,
            )
        return 'No desktop image set — the project cover will be used.'

    @admin.display(description='Phone preview')
    def carousel_mobile_preview(self, obj):
        if obj and obj.carousel_mobile_image:
            return format_html(
                '<img src="{}" alt="" style="max-width:180px; max-height:280px; '
                'object-fit:cover; border-radius:3px;" />',
                obj.carousel_mobile_image,
            )
        return 'No phone image set — the desktop carousel image or cover will be used.'

    def _upload_carousel_image(self, request, obj, form, upload_field, model_field):
        uploaded_file = form.cleaned_data.get(upload_field)
        if not uploaded_file:
            return

        try:
            result = cloudinary.uploader.upload(
                uploaded_file,
                folder='vast_projects/carousel',
                resource_type='image',
            )
            setattr(obj, model_field, result['secure_url'])
        except Exception as exc:
            self.message_user(
                request,
                f'{form.fields[upload_field].label} upload failed: {exc}',
                level='error',
            )

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

        self._upload_carousel_image(
            request,
            obj,
            form,
            'carousel_desktop_image_file',
            'carousel_desktop_image',
        )
        self._upload_carousel_image(
            request,
            obj,
            form,
            'carousel_mobile_image_file',
            'carousel_mobile_image',
        )

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


@admin.register(DailyAnalyticsMetric)
class DailyAnalyticsMetricAdmin(admin.ModelAdmin):
    list_display = ('date', 'metric', 'label', 'count')
    list_filter = ('metric', 'date')
    search_fields = ('label',)
    ordering = ('-date', 'metric', 'label')
    readonly_fields = ('date', 'metric', 'label', 'count')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'name', 'phone', 'project_type', 'status', 'email_status')
    list_filter = ('status', 'email_status', 'project_type', 'created_at')
    search_fields = ('name', 'phone', 'email', 'project_location', 'message')
    list_editable = ('status',)
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at', 'updated_at', 'name', 'phone', 'email', 'project_type',
        'project_location', 'preferred_call_time', 'message', 'email_status',
        'email_error', 'email_sent_at',
    )
    fieldsets = (
        ('Enquiry', {
            'fields': (
                'created_at', 'name', 'phone', 'email', 'project_type',
                'project_location', 'preferred_call_time', 'message',
            ),
        }),
        ('Follow-up', {'fields': ('status', 'internal_notes')}),
        ('Email delivery', {
            'fields': ('email_status', 'email_sent_at', 'email_error'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(CareerSubmission)
class CareerSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'name', 'email', 'years_experience', 'seeking_internship',
        'portfolio_available', 'status', 'email_status',
    )
    list_filter = ('status', 'email_status', 'seeking_internship', 'created_at')
    search_fields = ('name', 'email', 'skills', 'portfolio_link')
    list_editable = ('status',)
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at', 'updated_at', 'name', 'email', 'skills', 'years_experience',
        'seeking_internship', 'portfolio_link', 'portfolio_download',
        'email_status', 'email_error', 'email_sent_at',
    )
    fieldsets = (
        ('Application', {
            'fields': (
                'created_at', 'name', 'email', 'skills', 'years_experience',
                'seeking_internship', 'portfolio_link', 'portfolio_download',
            ),
        }),
        ('Follow-up', {'fields': ('status', 'internal_notes')}),
        ('Email delivery', {
            'fields': ('email_status', 'email_sent_at', 'email_error'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Portfolio', boolean=True)
    def portfolio_available(self, obj):
        return bool(obj.portfolio_data or obj.portfolio_link)

    @admin.display(description='Portfolio PDF')
    def portfolio_download(self, obj):
        if not obj or not obj.portfolio_data:
            return 'No PDF uploaded'
        url = reverse('admin:projects_careersubmission_download_portfolio', args=(obj.pk,))
        return format_html('<a href="{}">Download {}</a>', url, obj.portfolio_filename)

    def get_urls(self):
        return [
            path(
                '<path:object_id>/download-portfolio/',
                self.admin_site.admin_view(self.download_portfolio),
                name='projects_careersubmission_download_portfolio',
            ),
        ] + super().get_urls()

    def download_portfolio(self, request, object_id):
        submission = get_object_or_404(CareerSubmission, pk=object_id)
        if not submission.portfolio_data:
            raise Http404('No portfolio was uploaded for this application.')
        filename = submission.portfolio_filename or 'portfolio.pdf'
        response = HttpResponse(
            bytes(submission.portfolio_data),
            content_type=submission.portfolio_content_type or 'application/pdf',
        )
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
        return response

    def has_add_permission(self, request):
        return False


admin.site.register(Typology, TypologyAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectImage, ProjectImageAdmin)
admin.site.register(SubType, SubTypeAdmin)
admin.site.register(Discipline, TypologyAdmin)
