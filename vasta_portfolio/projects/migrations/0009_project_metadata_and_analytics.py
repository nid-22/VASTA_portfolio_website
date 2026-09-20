from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrate_project_metadata(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Discipline = apps.get_model('projects', 'Discipline')
    Discipline.objects.get_or_create(name='Architecture')
    Discipline.objects.get_or_create(name='Interior')

    # Preserve each project's existing category before the temporary many-to-many
    # field is removed. Keep this migration deliberately small so production data
    # cleanup can run independently after the schema is available.
    for project in Project.objects.prefetch_related('typologies'):
        old_category = project.typologies.first()
        if old_category:
            Project.objects.filter(pk=project.pk).update(category_id=old_category.pk)

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



