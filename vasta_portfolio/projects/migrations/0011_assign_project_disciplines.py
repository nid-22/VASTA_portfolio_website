from django.db import migrations


PROJECT_DISCIPLINES = {
    'Kanuvai Residence 01': ('Architecture', 'Interior'),
    'Kanuvai Residence 02': ('Architecture', 'Interior'),
    'Ranka Ankura': ('Architecture',),
    'SV Reddy Residence': ('Interior',),
    'Hotel SOHOCO': ('Architecture', 'Interior'),
    'Gymnasium, Karur': ('Architecture', 'Interior'),
    'Kadiri Convention Hall': ('Architecture',),
    'Abode TerraVista': ('Architecture',),
    'Abode Tranquil': ('Architecture',),
    'Abode TerraNova': ('Architecture',),
    'Salem Residence': ('Architecture',),
    "TNPL Bachelor's Hostel": ('Architecture',),
    'Giridhar interiors': ('Interior',),
    'Baygrape office interiors': ('Interior',),
    'TNPL Corporate Office': ('Interior',),
    'Vismaya Interiors': ('Interior',),
    'Ashokan Residence': ('Interior',),
    'Coonoor Residence': ('Architecture', 'Interior'),
    'Guest House, Karur': ('Architecture',),
    'TNPL Sales Office, Mumbai': ('Interior',),
    'Mandaveli Apartment': ('Architecture',),
    'New Andhra Restaurant': ('Interior',),
    'New Andhra Restaurant - 2': ('Interior',),
    '7 Peaks Cycles': ('Interior',),
    'Elevate 21': ('Interior',),
    'W. Mambalam Residence-1': ('Architecture',),
    'Domlur Residential Renovation': ('Interior',),
}


def assign_project_disciplines(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Discipline = apps.get_model('projects', 'Discipline')
    disciplines = {
        name: Discipline.objects.get_or_create(name=name)[0]
        for name in ('Architecture', 'Interior')
    }

    for heading, discipline_names in PROJECT_DISCIPLINES.items():
        project = Project.objects.filter(heading=heading).first()
        if project:
            project.disciplines.set([disciplines[name] for name in discipline_names])


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_project_content_cleanup'),
    ]

    operations = [
        migrations.RunPython(assign_project_disciplines, migrations.RunPython.noop),
    ]
