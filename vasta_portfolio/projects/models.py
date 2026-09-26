from django.db import models
from django.utils import timezone

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


class Discipline(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

status_choice = (
    ('Completed', 'Completed'),
    ('Ongoing', 'Ongoing'),
    ('Unbuilt', 'Unbuilt'),
)

class Project(BaseModel):
    heading = models.CharField(max_length=100, null=False, blank=False, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.TextField(null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    project_year = models.CharField(max_length=4,  null=False, blank=False)
    status = models.CharField(max_length=10, choices=status_choice, null=True)
    category = models.ForeignKey(
        Typology,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='categorized_projects',
        verbose_name='Project category',
    )
    disciplines = models.ManyToManyField(Discipline, blank=True, related_name='projects')
    sub_type = models.ForeignKey(SubType, on_delete=models.PROTECT, null=True)
    size = models.CharField(max_length=20,  null=False, blank=False)
    content = HTMLField(default="", null=True, blank=True)
    location = models.ForeignKey(Location,on_delete=models.PROTECT, null=True, blank=True)
    client = models.CharField(max_length=100, null=True, blank=True)
    cover_image = models.CharField(max_length=500, null=True, blank=True)
    carousel_desktop_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Desktop carousel image',
        help_text='Landscape image used by the homepage carousel on desktop and tablet.',
    )
    carousel_mobile_image = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Phone carousel image',
        help_text='Portrait image used by the homepage carousel on phones.',
    )
    show_in_carousel = models.BooleanField(
        default=True,
        verbose_name='Show in homepage carousel',
        help_text='Turn this off to keep the project on the website but exclude it from the homepage carousel.',
    )
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

    @property
    def category_label(self):
        return self.category.name if self.category else ''

    @property
    def discipline_filter_classes(self):
        classes = ' '.join(slugify(discipline.name) for discipline in self.disciplines.all())
        # Existing production projects have no discipline data yet. Keep them
        # visible in both filters until their admin checkboxes are assigned.
        return classes or 'architecture interior'

    @staticmethod
    def _clean_optional_text(value):
        if value is None or str(value).strip().lower() == 'none':
            return ''
        return value

    @property
    def display_short_description(self):
        return self._clean_optional_text(self.short_description)

    @property
    def display_long_description(self):
        return self._clean_optional_text(self.long_description)

    @property
    def desktop_carousel_image_url(self):
        """Prefer the desktop carousel image, then fall back to the cover."""
        return self.carousel_desktop_image or self.cover_image or ''

    @property
    def mobile_carousel_image_url(self):
        """Prefer the phone image, then desktop carousel image, then cover."""
        return (
            self.carousel_mobile_image
            or self.carousel_desktop_image
            or self.cover_image
            or ''
        )

class ProjectImage(BaseModel):
    """One image attached to a Project. Kept as a separate model so the
    admin can inline multiple images on the Project edit page.
    """
    project = models.ForeignKey(Project, related_name='project_images', on_delete=models.PROTECT)
    image = models.CharField(max_length=500)

    def __str__(self):
        return f"Image for {self.project.heading} ({self.pk})"


class DailyAnalyticsMetric(models.Model):
    PROJECT_VIEW = 'project_view'
    FORM_SUBMISSION = 'form_submission'
    NAVIGATION = 'navigation'
    METRIC_CHOICES = (
        (PROJECT_VIEW, 'Project view'),
        (FORM_SUBMISSION, 'Form submission'),
        (NAVIGATION, 'Navigation'),
    )

    date = models.DateField(default=timezone.localdate)
    metric = models.CharField(max_length=32, choices=METRIC_CHOICES)
    label = models.CharField(max_length=160)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-date', 'metric', 'label')
        constraints = [
            models.UniqueConstraint(fields=('date', 'metric', 'label'), name='unique_daily_analytics_metric'),
        ]

    def __str__(self):
        return f'{self.date} · {self.get_metric_display()} · {self.label}: {self.count}'


class SubmissionBase(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        CONTACTED = 'contacted', 'Contacted'
        IN_PROGRESS = 'in_progress', 'In progress'
        CLOSED = 'closed', 'Closed'
        SPAM = 'spam', 'Spam'

    class EmailStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        DISABLED = 'disabled', 'Disabled'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    internal_notes = models.TextField(blank=True)
    email_status = models.CharField(
        max_length=12,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
    )
    email_error = models.TextField(blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class ContactSubmission(SubmissionBase):
    PROJECT_TYPE_CHOICES = (
        ('architecture', 'Architecture'),
        ('interiors', 'Interior design'),
        ('architecture-interiors', 'Architecture + interiors'),
        ('landscape', 'Landscape'),
        ('other', 'Something else'),
    )

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    project_type = models.CharField(max_length=30, choices=PROJECT_TYPE_CHOICES)
    project_location = models.CharField(max_length=150, blank=True)
    preferred_call_time = models.CharField(max_length=100, blank=True)
    message = models.TextField(max_length=3000)

    def __str__(self):
        return f'{self.name} · {self.created_at:%d %b %Y}'


class CareerSubmission(SubmissionBase):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    skills = models.TextField(max_length=500, blank=True)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    seeking_internship = models.BooleanField(default=False)
    portfolio_link = models.URLField(max_length=500, blank=True)
    portfolio_filename = models.CharField(max_length=255, blank=True)
    portfolio_content_type = models.CharField(max_length=100, blank=True)
    portfolio_data = models.BinaryField(null=True, blank=True, editable=False)

    @property
    def has_portfolio_file(self):
        return bool(self.portfolio_data)

    def __str__(self):
        return f'{self.name} · {self.created_at:%d %b %Y}'


