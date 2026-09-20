from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0005_alter_project_cover_image_alter_projectimage_image'),
    ]

    operations = [
        # Migration 0005 already removed this column. The old redundant SQL
        # used PostgreSQL-only syntax and prevented fresh SQLite databases.
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
