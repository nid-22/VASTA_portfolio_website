from django import forms
from django.contrib import admin
from tinymce.widgets import TinyMCE
from .models import Blog
from django.utils.html import format_html


class BlogAdminForm(forms.ModelForm):
	class Meta:
		model = Blog
		fields = '__all__'
		widgets = {
			'content': TinyMCE(mce_attrs={
				'content_css': '/static/assets/css/editor_content.css?v=20260921-blog2',
				'content_style': 'body { font-family: Arial, sans-serif; line-height: 1.7; } table:has(img), table:has(img) th, table:has(img) td { border: 0 !important; outline: 0 !important; }',
				'toolbar': 'undo redo | blocks styles | bold italic underline | alignleft aligncenter alignright | bullist numlist | image table link | code',
				'style_formats': [
					{'title': 'Image left, text wraps', 'selector': 'figure.image', 'classes': 'essay-float-left'},
					{'title': 'Image right, text wraps', 'selector': 'figure.image', 'classes': 'essay-float-right'},
					{'title': 'Two images side by side', 'selector': 'table', 'classes': 'essay-image-pair'},
				],
				'image_caption': True,
				'image_class_list': [
					{'title': 'In text column', 'value': ''},
					{'title': 'Align left, wrap text', 'value': 'essay-float-left'},
					{'title': 'Align right, wrap text', 'value': 'essay-float-right'},
				],
				'table_class_list': [
					{'title': 'Regular table', 'value': ''},
					{'title': 'Two images side by side', 'value': 'essay-image-pair'},
				],
			}),
		}


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
	form = BlogAdminForm
	list_display = ('title', 'is_active', 'created_date', 'total_read_time', 'cover_image_thumb')
	list_filter = ('is_active', 'created_date')
	search_fields = ('title', 'short_description', 'content')
	prepopulated_fields = {'slug': ('title',)}
	ordering = ('-created_date',)
	fieldsets = (
		(None, {'fields': ('title', 'slug', 'is_active', 'short_description', 'cover_image', 'total_read_time', 'content_width')}),
		('Essay', {'fields': ('content',), 'description': 'For a caption, select an image and turn on Caption in the image dialog. For paired images, insert a two-column table, choose “Two images side by side” in Table properties, and place one captioned image in each cell. For text wrapping, select Left or Right in the image Class menu.'}),
	)

	def cover_image_thumb(self, obj):
		if obj.cover_image:
			return format_html('<img src="{}" style="height:40px;" />', obj.cover_image.url)
		return '-'

	cover_image_thumb.short_description = 'Cover'
