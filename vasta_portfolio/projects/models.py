from django.db import models

from django.utils.text import slugify
from django.urls import reverse

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

# choices for grid shape used by front-end Isotope/Masonry layout
GRID_SHAPE_CHOICES = (
    ('rect_tall', 'Rect Tall'),
    ('rect_wide', 'Rect Wide'),
    ('square_small', 'Square Small'),
    ('square_large', 'Square Large'),
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
    # grid_shape controls how this project will be sized in the grid
    grid_shape = models.CharField(max_length=20, choices=GRID_SHAPE_CHOICES, default='square_small', help_text='Grid tile shape for portfolio layout')
    location = models.ForeignKey(Location,on_delete=models.PROTECT, null=True, blank=True)
    client = models.CharField(max_length=100, null=True, blank=True)
    cover_image = models.ImageField(upload_to='media/cover_images/', null=True, blank=True)
    cover_image_big = models.ImageField(upload_to='media/cover_images/', null=True, blank=True)

    def __str__(self):
        return self.heading

    def save(self,*args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)
        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug':self.slug})

class ProcessImages(BaseModel):
    project = models.ForeignKey(Project, related_name='process_images', on_delete=models.PROTECT)
    image = models.ImageField(upload_to='media/process_images/')


