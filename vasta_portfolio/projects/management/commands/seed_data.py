import random

from django.core.management.base import BaseCommand

from projects.models import Project, Typology, SubType, Location


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


# ---------------------------------------------------------------------------
# Source of truth: the project spreadsheet (Vast Architects website sheet).
# "Dropped" projects are excluded. Sheet statuses are mapped onto the model's
# two allowed choices:
#     Completed                                        -> Complete
#     On site / Design Stage / Nearing Completion      -> Ongoing
#
# Short/long descriptions from the supplied write-ups are attached to the
# sheet rows they correspond to.
#
# project_year: random 2023-2025 (sheet completion dates were blank)
# size:         random 2000-4000 sq ft
# content:      empty
# ---------------------------------------------------------------------------

PROJECTS = [
    {
        'sno': 1,
        'heading': 'Ranka Junction',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Commercial',
        'sub_type': None,
    },
    {
        'sno': 2,
        'heading': 'Baygrape office interiors',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Workplace',
        'sub_type': 'Corporate Office',
        'short_description': 'A premium office renovation designed to encourage collaboration, community, and focused, enjoyable work.',
        'long_description': 'The Baygrape office interiors create a refined yet energetic workplace. Premium materials, customized detailing, and open layouts encourage collaboration and discussion, while focused work zones support productivity, balancing professionalism with warmth and everyday usability.',
    },
    {
        'sno': 4,
        'heading': 'Kumara Park Apartment',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Apartment',
        'short_description': 'Traditional South Indian interiors crafted in solid wood, expressing strength, timelessness, and adaptable living.',
        'long_description': 'These Kumara Park apartment interiors draw from traditional South Indian themes. Solid wood, sturdy detailing, and timeless proportions create strong, durable spaces that feel rooted in craftsmanship, while remaining flexible enough to adapt to contemporary living needs.',
    },
    {
        'sno': 5,
        'heading': 'Jalahalli Elevation',
        'status': 'Ongoing',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 6,
        'heading': 'Abode South - TerraVista',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 7,
        'heading': '7 Peaks Cycles',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Retail',
        'sub_type': 'Store',
        'short_description': 'A vibrant, mountain-inspired retail space designed to energize users and highlight premium cycling products.',
        'long_description': '7 Peaks Cycles is designed as a bright, mountain-inspired retail space. Bold colours, active layouts, and well-crafted display units highlight premium products, creating an attractive, welcoming environment that encourages exploration, movement, and customer engagement.',
    },
    {
        'sno': 8,
        'heading': 'Yelahanka SV Reddy',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
        'short_description': 'A warm, luxurious residence blending refined interiors and landscape through soft materials and thoughtful detailing.',
        'long_description': 'Set in Yelahanka, this residence blends luxury with warmth through soft materials, rich wood, and marble. Detailed interiors and a seamless landscape connection create calm, welcoming spaces that feel refined yet comfortable, designed for everyday living with understated elegance.',
    },
    {
        'sno': 9,
        'heading': 'Betalsur Studio Apartments',
        'status': 'Ongoing',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 11,
        'heading': 'Thiruvanmiyur Apartment',
        'status': 'Complete',
        'city': 'Chennai',
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 12,
        'heading': 'Ranka Ankura',
        'status': 'Ongoing',
        'city': 'Bengaluru',
        'typology': 'Commercial',
        'sub_type': 'Office Building',
        'short_description': 'A dominant, welcoming clubhouse designed as the visual and social heart of the community.',
        'long_description': 'Positioned at the site entrance, the Ranka Ankura Clubhouse is designed as an immediate focal point. Earthy materials are paired with modern forms and large glass walls to create openness. Spacious rooms, viewing decks, and covered porticos support community interaction and visual connection.',
    },
    {
        'sno': 13,
        'heading': "TNPL Bachelor's Hostel",
        'status': 'Complete',
        'city': 'Trichy',
        'typology': 'Hospitality',
        'sub_type': 'Boutique Hotel',
        'short_description': 'A calm, balanced hostel designed with strong form, monotone expression, and generous landscaped openness.',
        'long_description': 'Designed for clarity and calm, the TNPL Bachelor Hostel uses a strong, balanced form with monotone finishes. Landscaped open areas and generous spaces create a democratic, breathable environment that supports comfort, routine, and mental ease for everyday living.',
    },
    {
        'sno': 14,
        'heading': 'Sidharth Shah RCS',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 15,
        'heading': 'Jagdish Rajaram RCS',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 16,
        'heading': 'Abode North Facing',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 17,
        'heading': 'Giridhar interiors',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 19,
        'heading': 'Ram Kalyanasundaram RCS',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 20,
        'heading': '002 OPV Anupama Apartment',
        'status': 'Complete',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 21,
        'heading': 'Peenya Factory',
        'status': 'Ongoing',
        'city': 'Bengaluru',
        'typology': 'Commercial',
        'sub_type': None,
    },
    {
        'sno': 22,
        'heading': 'TNPL Corporate - 3rd Floor',
        'status': 'Complete',
        'city': 'Chennai',
        'typology': 'Workplace',
        'sub_type': 'Corporate Office',
    },
    {
        'sno': 23,
        'heading': 'TNPL Gym - Karur',
        'status': 'Complete',
        'city': 'Karur',
        'typology': 'Commercial',
        'sub_type': None,
    },
    {
        'sno': 24,
        'heading': 'Niraj Residence',
        'status': 'Ongoing',
        'city': 'Bengaluru',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 25,
        'heading': 'DAV School',
        'status': 'Complete',
        'city': None,
        'typology': 'Commercial',
        'sub_type': None,
    },
    {
        'sno': 26,
        'heading': 'Asif Residence',
        'status': 'Complete',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
        'short_description': 'A richly detailed, luxury home where craftsmanship and Mughal-inspired elegance define every space.',
        'long_description': 'The Asif Residence is a celebration of meticulous design and craftsmanship. Every nook is carefully detailed, reflecting labor-intensive work and close attention. Inspired by Mughal aesthetics, the home expresses a royal, luxurious character through rich materials, ornate detailing, and refined spatial composition.',
    },
    {
        'sno': 28,
        'heading': 'Ravi Babu Residence',
        'status': 'Complete',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 29,
        'heading': 'Abode TerraNova',
        'status': 'Complete',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 30,
        'heading': 'Amara Vana Interiors',
        'status': 'Complete',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 31,
        'heading': 'Mandaveli Apartment',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 32,
        'heading': 'Dhanakodi Residence',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 33,
        'heading': 'Sundar Rajan Residence',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 34,
        'heading': 'TNPL 4th floor',
        'status': 'Complete',
        'city': None,
        'typology': 'Workplace',
        'sub_type': 'Corporate Office',
    },
    {
        'sno': 35,
        'heading': 'New Andhra Restaurant',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Hospitality',
        'sub_type': 'Restaurant',
        'short_description': 'A contemporary restaurant rooted in tradition, celebrating history, culture, and efficiency.',
        'long_description': 'Designed in Chennai, the New Andhra Restaurant draws from traditional Indian aesthetics with an artsy, historical sensibility. While rich in cultural expression, the layout is carefully planned for operational efficiency, creating a dining experience that balances visual appeal with functionality and spirit.',
    },
    {
        'sno': 36,
        'heading': 'Anantpur Convention Hall',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Commercial',
        'sub_type': None,
    },
    {
        'sno': 38,
        'heading': 'W. Mambalam Residence',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
    {
        'sno': 39,
        'heading': 'Elevate 21',
        'status': 'Complete',
        'city': None,
        'typology': 'Residential',
        'sub_type': 'Apartment',
    },
    {
        'sno': 40,
        'heading': 'TNPL 6th floor + ground floor',
        'status': 'Complete',
        'city': None,
        'typology': 'Workplace',
        'sub_type': 'Corporate Office',
    },
    {
        'sno': 41,
        'heading': 'New Andhra Restaurant - 2',
        'status': 'Ongoing',
        'city': None,
        'typology': 'Hospitality',
        'sub_type': 'Restaurant',
    },
    {
        'sno': 42,
        'heading': 'TNPLSales Office, Mumbai',
        'status': 'Complete',
        'city': 'Mumbai',
        'typology': 'Workplace',
        'sub_type': 'Corporate Office',
    },
    {
        'sno': 43,
        'heading': 'Coonoor Residence',
        'status': 'Ongoing',
        'city': 'Coonoor',
        'typology': 'Residential',
        'sub_type': 'Private House',
    },
]


class Command(BaseCommand):
    help = 'Seed Typology, SubType, Location, and Project data (idempotent)'

    def handle(self, *args, **options):
        # --- Reference / lookup data ------------------------------------
        for name in TYPOLOGIES:
            _, created = Typology.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} Typology: {name}")

        for name in SUBTYPES:
            _, created = SubType.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} SubType: {name}")

        for name in LOCATIONS:
            _, created = Location.objects.get_or_create(name=name)
            self.stdout.write(f"{'Created' if created else 'Exists'} Location: {name}")

        # --- Projects ---------------------------------------------------
        for data in PROJECTS:
            typology, _ = Typology.objects.get_or_create(name=data['typology'])

            sub_type = None
            if data.get('sub_type'):
                sub_type, _ = SubType.objects.get_or_create(name=data['sub_type'])

            location = None
            if data.get('city'):
                location, _ = Location.objects.get_or_create(name=data['city'])

            _, created = Project.objects.get_or_create(
                heading=data['heading'],
                defaults={
                    'short_description': data.get('short_description'),
                    'long_description': data.get('long_description'),
                    'project_year': str(random.randint(2023, 2025)),
                    'status': data['status'],
                    'typology': typology,
                    'sub_type': sub_type,
                    'size': f"{random.randint(2000, 4000)} sq ft",
                    'content': '',
                    'location': location,
                    'order_to_display_id': data['sno'],
                },
            )
            self.stdout.write(
                f"{'Created' if created else 'Exists'} Project: {data['heading']}"
            )

        self.stdout.write(
            self.style.SUCCESS(f'Seeding complete ({len(PROJECTS)} projects).')
        )
