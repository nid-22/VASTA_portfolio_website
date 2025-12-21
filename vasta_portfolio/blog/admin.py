from django.contrib import admin
from .models import Blog
from django.utils.html import format_html


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active', 'created_date', 'total_read_time', 'cover_image_thumb')
	list_filter = ('is_active', 'created_date')
	search_fields = ('title', 'short_description', 'content')
	prepopulated_fields = {'slug': ('title',)}
	ordering = ('-created_date',)

	def cover_image_thumb(self, obj):
		if obj.cover_image:
			return format_html('<img src="{}" style="height:40px;" />', obj.cover_image.url)
		return '-'

	cover_image_thumb.short_description = 'Cover'
