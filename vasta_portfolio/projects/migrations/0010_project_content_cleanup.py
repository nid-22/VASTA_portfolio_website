from django.db import migrations


def clean_project_content(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Typology = apps.get_model('projects', 'Typology')
    SubType = apps.get_model('projects', 'SubType')

    for project in Project.objects.all().only('pk', 'short_description', 'long_description'):
        updates = {}
        for field_name in ('short_description', 'long_description'):
            value = getattr(project, field_name)
            if value and value.strip().casefold() == 'none':
                updates[field_name] = None
        if updates:
            Project.objects.filter(pk=project.pk).update(**updates)

    hotel = Project.objects.filter(heading__iexact='Hotel SOHOCO').first()
    if hotel:
        hospitality_category = Typology.objects.filter(name__iexact='Hospitality').first()
        if not hospitality_category:
            hospitality_category = Typology.objects.create(name='Hospitality')
        hospitality_subtype = SubType.objects.filter(name__iexact='Hospitality').first()
        if not hospitality_subtype:
            hospitality_subtype = SubType.objects.create(name='Hospitality')
        Project.objects.filter(pk=hotel.pk).update(
            category_id=hospitality_category.pk,
            sub_type_id=hospitality_subtype.pk,
        )

    salem = Project.objects.filter(heading__iexact='Salem Residence').first()
    if salem:
        updates = {
            'short_description': (
                'A home shaped by connected volumes and natural light, the architecture aims '
                'to bring together life, light and landscape.'
            ),
            'content': (salem.content or '').replace(
                'while not maintaining the simplicity of a weekend home',
                'while maintaining the simplicity of a weekend home',
            ),
        }
        desired_slug = 'salem-residence'
        if not Project.objects.exclude(pk=salem.pk).filter(slug=desired_slug).exists():
            updates['slug'] = desired_slug
        Project.objects.filter(pk=salem.pk).update(**updates)

    mambalam = Project.objects.filter(heading__iexact='W. Mambalam Residence-1').first()
    if mambalam:
        Project.objects.filter(pk=mambalam.pk).update(
            long_description=(
                'West Mambalam Residence 1 is an interior scheme that blends classical warmth '
                'with contemporary comfort. Rich teak-toned woodwork runs through the home—a '
                'carved-detail bedroom, backlit arched display niches, a cosy timber-framed '
                'window seat, and an open living-dining space anchored by a traditional display '
                'cabinet—creating a refined, rooted and inviting family environment.'
            )
        )


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0009_project_metadata_and_analytics'),
    ]

    operations = [
        migrations.RunPython(clean_project_content, migrations.RunPython.noop),
    ]
