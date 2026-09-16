from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_remove_project_grid_shape'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='carousel_desktop_image',
            field=models.URLField(
                blank=True,
                help_text='Landscape image used by the homepage carousel on desktop and tablet.',
                max_length=500,
                null=True,
                verbose_name='Desktop carousel image',
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='carousel_mobile_image',
            field=models.URLField(
                blank=True,
                help_text='Portrait image used by the homepage carousel on phones.',
                max_length=500,
                null=True,
                verbose_name='Phone carousel image',
            ),
        ),
    ]
