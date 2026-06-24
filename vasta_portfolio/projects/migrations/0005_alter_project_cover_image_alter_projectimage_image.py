from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_alter_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='cover_image',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='projectimage',
            name='image',
            field=models.CharField(max_length=500),
        ),
        migrations.RemoveField(
            model_name='project',
            name='grid_shape',
        ),
    ]
