"""
Management command to seed initial data
"""
from django.core.management.base import BaseCommand
from apps.plans.models import Plan, InvitationCategory, Template


class Command(BaseCommand):
    help = 'Seed initial plans, categories, and templates'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        
        # Create Plans
        self.create_plans()
        
        # Create Categories
        self.create_categories()
        
        # Create Templates
        self.create_templates()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded data'))
    
    def create_plans(self):
        self.stdout.write('Creating plans...')
        
        plans_data = [
            {
                'code': 'BASIC',
                'name': 'Basic',
                'description': 'Perfect for small gatherings and personal events',
                'regular_links': 100,
                'test_links': 5,
                'price_inr': 150,
                'features': [
                    '100 invitation links',
                    '5 test links',
                    'Basic templates',
                    '15 days validity',
                    'Email support'
                ],
                'sort_order': 1
            },
            {
                'code': 'PREMIUM',
                'name': 'Premium',
                'description': 'Ideal for weddings and medium-sized events',
                'regular_links': 150,
                'test_links': 5,
                'price_inr': 350,
                'features': [
                    '150 invitation links',
                    '5 test links',
                    'Basic + Premium templates',
                    '15 days validity',
                    'Priority support',
                    'Gallery support',
                    'Custom colors'
                ],
                'sort_order': 2
            },
            {
                'code': 'LUXURY',
                'name': 'Luxury',
                'description': 'The ultimate experience for grand celebrations',
                'regular_links': 200,
                'test_links': 5,
                'price_inr': 500,
                'features': [
                    '200 invitation links',
                    '5 test links',
                    'All templates including Luxury',
                    '15 days validity',
                    'VIP support',
                    'Gallery & Music support',
                    'Custom animations',
                    'Priority processing'
                ],
                'sort_order': 3
            }
        ]
        
        for plan_data in plans_data:
            Plan.objects.get_or_create(
                code=plan_data['code'],
                defaults=plan_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(plans_data)} plans'))
    
    def create_categories(self):
        self.stdout.write('Creating categories...')
        
        categories_data = [
            {'code': 'WEDDING', 'name': 'Wedding', 'description': 'Wedding invitations', 'icon': 'Favorite', 'sort_order': 1},
            {'code': 'BIRTHDAY', 'name': 'Birthday', 'description': 'Birthday invitations', 'icon': 'Cake', 'sort_order': 2},
            {'code': 'PARTY', 'name': 'Party', 'description': 'Party invitations', 'icon': 'Celebration', 'sort_order': 3},
            {'code': 'EID', 'name': 'Eid', 'description': 'Eid Mubarak invitations', 'icon': 'Mosque', 'sort_order': 4},
            {'code': 'DIWALI', 'name': 'Diwali', 'description': 'Diwali invitations', 'icon': 'TempleHindu', 'sort_order': 5},
            {'code': 'CHRISTMAS', 'name': 'Christmas', 'description': 'Christmas invitations', 'icon': 'Church', 'sort_order': 6},
            {'code': 'RAMZAN', 'name': 'Ramzan', 'description': 'Ramzan invitations', 'icon': 'Mosque', 'sort_order': 7},
            {'code': 'HOUSE_WARMING', 'name': 'House Warming', 'description': 'House warming invitations', 'icon': 'Home', 'sort_order': 8},
            {'code': 'ENGAGEMENT', 'name': 'Engagement', 'description': 'Engagement invitations', 'icon': 'Favorite', 'sort_order': 9},
            {'code': 'BABY_SHOWER', 'name': 'Baby Shower', 'description': 'Baby shower invitations', 'icon': 'ChildCare', 'sort_order': 10},
        ]
        
        for cat_data in categories_data:
            InvitationCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories_data)} categories'))
    
    def create_templates(self):
        self.stdout.write('Creating templates...')
        
        # Get plans
        basic_plan = Plan.objects.get(code='BASIC')
        premium_plan = Plan.objects.get(code='PREMIUM')
        luxury_plan = Plan.objects.get(code='LUXURY')
        
        # Get categories
        wedding_cat = InvitationCategory.objects.get(code='WEDDING')
        birthday_cat = InvitationCategory.objects.get(code='BIRTHDAY')
        party_cat = InvitationCategory.objects.get(code='PARTY')
        eid_cat = InvitationCategory.objects.get(code='EID')
        diwali_cat = InvitationCategory.objects.get(code='DIWALI')
        
        templates_data = [
            # Wedding Templates
            {
                'plan': basic_plan,
                'category': wedding_cat,
                'name': 'Elegant Wedding',
                'description': 'Classic elegant wedding invitation with gold accents',
                'animation_type': 'elegant',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
            {
                'plan': basic_plan,
                'category': wedding_cat,
                'name': 'Floral Wedding',
                'description': 'Beautiful floral themed wedding invitation',
                'animation_type': 'floral',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
            {
                'plan': premium_plan,
                'category': wedding_cat,
                'name': 'Royal Wedding',
                'description': 'Grand royal wedding invitation with red and gold',
                'animation_type': 'royal',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
                'is_premium': True,
            },
            {
                'plan': luxury_plan,
                'category': wedding_cat,
                'name': 'Bollywood Wedding',
                'description': 'Dramatic Bollywood style wedding invitation',
                'animation_type': 'bollywood',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
                'is_premium': True,
            },
            
            # Birthday Templates
            {
                'plan': basic_plan,
                'category': birthday_cat,
                'name': 'Fun Birthday',
                'description': 'Colorful and fun birthday invitation',
                'animation_type': 'fun',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
            {
                'plan': premium_plan,
                'category': birthday_cat,
                'name': 'Modern Birthday',
                'description': 'Sleek modern birthday invitation',
                'animation_type': 'modern',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
                'is_premium': True,
            },
            
            # Party Templates
            {
                'plan': basic_plan,
                'category': party_cat,
                'name': 'Party Night',
                'description': 'Exciting party invitation with vibrant colors',
                'animation_type': 'fun',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
            
            # Festival Templates
            {
                'plan': basic_plan,
                'category': eid_cat,
                'name': 'Eid Mubarak',
                'description': 'Beautiful Eid invitation with moon and stars',
                'animation_type': 'traditional',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
            {
                'plan': basic_plan,
                'category': diwali_cat,
                'name': 'Diwali Celebration',
                'description': 'Festive Diwali invitation with diyas and lights',
                'animation_type': 'traditional',
                'theme_colors': {'primary': '#A61E2A', 'secondary': '#2E2E2E', 'accent': '#D9D9D9', 'background': '#F5F2ED'},
            },
        ]
        
        for template_data in templates_data:
            Template.objects.get_or_create(
                name=template_data['name'],
                plan=template_data['plan'],
                category=template_data['category'],
                defaults={
                    'description': template_data['description'],
                    'animation_type': template_data['animation_type'],
                    'theme_colors': template_data.get('theme_colors', {}),
                    'is_premium': template_data.get('is_premium', False),
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(templates_data)} templates'))
