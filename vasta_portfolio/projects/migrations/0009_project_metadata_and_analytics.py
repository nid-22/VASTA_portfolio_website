from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrate_project_metadata(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Discipline = apps.get_model('projects', 'Discipline')
    architecture, _ = Discipline.objects.get_or_create(name='Architecture')
    interior, _ = Discipline.objects.get_or_create(name='Interior')

    for project in Project.objects.prefetch_related('typologies'):
        old_categories = list(project.typologies.all())
        if old_categories:
            project.category_id = old_categories[0].id
            project.save(update_fields=['category'])
            for old_category in old_categories:
                if old_category.name.casefold() == 'architecture':
                    project.disciplines.add(architecture)
                elif old_category.name.casefold() in ('interior', 'interiors'):
                    project.disciplines.add(interior)

        updates = []
        for field_name in ('short_description', 'long_description'):
            value = getattr(project, field_name)
            if value and value.strip().casefold() == 'none':
                setattr(project, field_name, None)
                updates.append(field_name)
        if updates:
            project.save(update_fields=updates)

    hotel = Project.objects.filter(heading__iexact='Hotel SOHOCO').first()
    if hotel:
        Typology = apps.get_model('projects', 'Typology')
        SubType = apps.get_model('projects', 'SubType')
        hospitality_category = Typology.objects.filter(name__iexact='Hospitality').first()
        if not hospitality_category:
            hospitality_category = Typology.objects.create(name='Hospitality')
        hospitality_subtype = SubType.objects.filter(name__iexact='Hospitality').first()
        if not hospitality_subtype:
            hospitality_subtype = SubType.objects.create(name='Hospitality')
        hotel.category = hospitality_category
        hotel.sub_type = hospitality_subtype
        hotel.save(update_fields=['category', 'sub_type'])

    salem = Project.objects.filter(heading__iexact='Salem Residence').first()
    if salem:
        desired_slug = 'salem-residence'
        if not Project.objects.exclude(pk=salem.pk).filter(slug=desired_slug).exists():
            salem.slug = desired_slug
        salem.short_description = (
            'A home shaped by connected volumes and natural light, the architecture aims '
            'to bring together life, light and landscape.'
        )
        salem.content = (salem.content or '').replace(
            'while not maintaining the simplicity of a weekend home',
            'while maintaining the simplicity of a weekend home',
        )
        salem.save(update_fields=['slug', 'short_description', 'long_description', 'content'])

    mambalam = Project.objects.filter(heading__iexact='W. Mambalam Residence-1').first()
    if mambalam:
        mambalam.long_description = (
            'West Mambalam Residence 1 is an interior scheme that blends classical warmth '
            'with contemporary comfort. Rich teak-toned woodwork runs through the home—a '
            'carved-detail bedroom, backlit arched display niches, a cosy timber-framed '
            'window seat, and an open living-dining space anchored by a traditional display '
            'cabinet—creating a refined, rooted and inviting family environment.'
        )
        mambalam.save(update_fields=['long_description'])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_project_typologies_and_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discipline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='categorized_projects', to='projects.typology', verbose_name='Project category'),
        ),
        migrations.AddField(
            model_name='project',
            name='disciplines',
            field=models.ManyToManyField(blank=True, related_name='projects', to='projects.discipline'),
        ),
        migrations.AlterField(
            model_name='project',
            name='short_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='long_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_project_metadata, migrations.RunPython.noop),
        migrations.RemoveField(model_name='project', name='typologies'),
        migrations.CreateModel(
            name='DailyAnalyticsMetric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('metric', models.CharField(choices=[('project_view', 'Project view'), ('form_submission', 'Form submission'), ('navigation', 'Navigation')], max_length=32)),
                ('label', models.CharField(max_length=160)),
                ('count', models.PositiveIntegerField(default=0)),
            ],
            options={'ordering': ('-date', 'metric', 'label')},
        ),
        migrations.AddConstraint(
            model_name='dailyanalyticsmetric',
            constraint=models.UniqueConstraint(fields=('date', 'metric', 'label'), name='unique_daily_analytics_metric'),
        ),
    ]

