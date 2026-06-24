from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_alter_project_cover_image_alter_projectimage_image'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE projects_project DROP COLUMN IF EXISTS grid_shape;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
