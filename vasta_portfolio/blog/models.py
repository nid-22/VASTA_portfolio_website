from django.db import models
from django.urls import reverse
from tinymce.models import HTMLField


class Blog(models.Model):
	title = models.CharField(max_length=255)
	short_description = models.TextField(max_length=500, blank=True)
	content = HTMLField(default="", null=True, blank=True)
	total_read_time = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated read time in minutes")
	cover_image = models.ImageField(upload_to='blog/cover_images/', null=True, blank=True)
	slug = models.SlugField(max_length=255, unique=True)
	is_active = models.BooleanField(default=True)
	created_date = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_date']

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse('blog:detail', args=[self.slug])
