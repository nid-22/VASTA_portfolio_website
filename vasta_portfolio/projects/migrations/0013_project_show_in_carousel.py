from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0012_careersubmission_contactsubmission'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='show_in_carousel',
            field=models.BooleanField(
                default=True,
                help_text='Turn this off to keep the project on the website but exclude it from the homepage carousel.',
                verbose_name='Show in homepage carousel',
            ),
        ),
    ]
