from django.db import models

from django.utils.text import slugify
from django.urls import reverse

from tinymce.models import HTMLField

# Create your models here.
class BaseModel(models.Model):
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract=True


class Typology(BaseModel):
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name

class Location(BaseModel):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

class SubType(BaseModel):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)

    def __str__(self):
        return self.name

status_choice = (
    ('Ongoing','Ongoing'),
    ('Complete','Complete'),
)

class Project(BaseModel):
    heading = models.CharField(max_length=100, null=False, blank=False, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300, null=True, blank=True)
    long_description = models.CharField(max_length=368,  null=True, blank=True)
    project_year = models.CharField(max_length=4,  null=False, blank=False)
    status = models.CharField(max_length=10, choices=status_choice, null=True)
    typology = models.ForeignKey(Typology,on_delete=models.PROTECT)
    sub_type = models.ForeignKey(SubType, on_delete=models.PROTECT, null=True)
    size = models.CharField(max_length=20,  null=False, blank=False)
    content = HTMLField(default="", null=True, blank=True)
    location = models.ForeignKey(Location,on_delete=models.PROTECT, null=True, blank=True)
    client = models.CharField(max_length=100, null=True, blank=True)
    cover_image = models.CharField(max_length=500, null=True, blank=True)
    # ordering integer for display in the portfolio grid (smaller numbers show first)
    order_to_display_id = models.PositiveIntegerField(default=0, help_text='Lower values appear earlier in the list')

    def __str__(self):
        return self.heading

    def save(self,*args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug':self.slug})

class ProjectImage(BaseModel):
    """One image attached to a Project. Kept as a separate model so the
    admin can inline multiple images on the Project edit page.
    """
    project = models.ForeignKey(Project, related_name='project_images', on_delete=models.PROTECT)
    image = models.CharField(max_length=500)

    def __str__(self):
        return f"Image for {self.project.heading} ({self.pk})"


