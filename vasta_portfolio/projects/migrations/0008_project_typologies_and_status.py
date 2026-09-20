from django.db import migrations, models


def copy_typology_to_many_to_many(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    through = Project.typologies.through
    rows = [
        through(project_id=project.id, typology_id=project.typology_id)
        for project in Project.objects.exclude(typology_id=None)
    ]
    through.objects.bulk_create(rows, ignore_conflicts=True)


def normalize_status(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Project.objects.filter(status='Complete').update(status='Completed')


def denormalize_status(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Project.objects.filter(status='Completed').update(status='Complete')


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_project_carousel_images'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='typologies',
            field=models.ManyToManyField(blank=True, related_name='projects', to='projects.typology'),
        ),
        migrations.RunPython(copy_typology_to_many_to_many, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='project',
            name='typology',
        ),
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(
                choices=[('Completed', 'Completed'), ('Ongoing', 'Ongoing'), ('Unbuilt', 'Unbuilt')],
                max_length=10,
                null=True,
            ),
        ),
        migrations.RunPython(normalize_status, denormalize_status),
    ]
