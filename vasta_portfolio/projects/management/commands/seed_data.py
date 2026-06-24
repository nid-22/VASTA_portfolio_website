from django.core.management.base import BaseCommand
from projects.models import Typology, SubType, Location


TYPOLOGIES = [
    'Residential',
    'Hospitality',
    'Workplace',
    'Retail',
    'Commercial',
]

SUBTYPES = [
    'Apartment',
    'Private House',
    'Boutique Hotel',
    'Restaurant',
    'Corporate Office',
    'Store',
    'Supermarket',
    'Office Building',
]

LOCATIONS = [
    'Coimbatore',
    'Bangalore',
    'Chennai',
    'Mumbai',
]


class Command(BaseCommand):
    help = 'Seed Typology, SubType, and Location data'

    def handle(self, *args, **options):
        for name in TYPOLOGIES:
            obj, created = Typology.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} Typology: {name}")

        for name in SUBTYPES:
            obj, created = SubType.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} SubType: {name}")

        for name in LOCATIONS:
            obj, created = Location.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} Location: {name}")

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
