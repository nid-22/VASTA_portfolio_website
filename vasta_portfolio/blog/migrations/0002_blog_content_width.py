from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blog',
            name='content_width',
            field=models.CharField(
                choices=[('compact', 'Compact (680 px)'), ('standard', 'Standard (780 px)'), ('wide', 'Wide (900 px)')],
                default='compact',
                help_text='Maximum width of the article text on desktop. Images can use their own alignment or a two-column table.',
                max_length=10,
            ),
        ),
    ]
