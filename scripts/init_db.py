"""
SC AI Lead Generation System - Database Initialization
Run this script to create all database tables
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.database.models import Base


def init_database():
    """Initialize the database with all tables"""
    print("🔧 Initializing SC AI Lead Generation Database...")
    print("=" * 50)
    
    try:
        # Create all tables
        db_manager.create_tables()
        print("\n✅ Database tables created successfully!")
        
        # Seed initial personas
        seed_personas()
        
        print("\n🎉 Database initialization complete!")
        print("=" * 50)
        print("\n📝 Next steps:")
        print("1. Update your .env file with credentials")
        print("2. Run: python backend/app.py")
        print("3. Visit: http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        sys.exit(1)


def seed_personas():
    """Seed initial persona data from Targets.docx"""
    print("\n📊 Seeding persona data...")
    
    personas = [
        {
            'name': 'Plastic Surgeon',
            'description': 'The Prestige Provider',
            'age_range': '40-65',
            'gender_distribution': 'Predominantly male',
            'goals': 'Attract high-value cosmetic cases, build strong regional reputation, fill schedule with elective procedures',
            'pain_points': 'Competing with med-spas offering cheaper treatments, inconsistent patient flow, website doesn\'t reflect brand quality',
            'key_message': 'Grow your reputation and patient bookings with proven digital systems built for plastic surgeons.',
            'message_tone': 'Consultative, prestige-focused'
        },
        {
            'name': 'Dermatologist',
            'description': 'The Clinical Authority',
            'age_range': '35-60',
            'gender_distribution': 'Mix of male/female',
            'goals': 'Balance medical and aesthetic clients, increase bookings for injectables and lasers, enhance online visibility',
            'pain_points': 'Limited marketing time, weak online reviews or local SEO, not converting enough cosmetic leads',
            'key_message': 'Expand your aesthetic revenue with results-driven marketing for dermatology practices.',
            'message_tone': 'Clinical authority, results-driven'
        },
        {
            'name': 'Med Spa Owner',
            'description': 'The Growth Seeker',
            'age_range': '30-55',
            'gender_distribution': 'Often female entrepreneurs',
            'goals': 'Consistent monthly bookings for injectables and treatments, scale brand awareness, automate client retention',
            'pain_points': 'High local competition, poor ad performance or tracking, weak branding or inconsistent visuals',
            'key_message': 'Dominate your local market with data-backed campaigns that turn browsers into loyal med-spa clients.',
            'message_tone': 'Growth-oriented, data-backed'
        },
        {
            'name': 'Day Spa',
            'description': 'The Relaxation Brand Builder',
            'age_range': '35-60',
            'gender_distribution': 'Mostly female ownership',
            'goals': 'Attract consistent appointments for skincare and wellness, improve Google and social visibility, retain clients through memberships',
            'pain_points': 'Low repeat-visit rates, inconsistent messaging or outdated website, competing with chain spas',
            'key_message': 'Build a recognizable, trusted spa brand with targeted marketing and retention systems.',
            'message_tone': 'Brand-building, retention-focused'
        },
        {
            'name': 'Wellness Center',
            'description': 'The Holistic Healer',
            'age_range': '30-60',
            'gender_distribution': 'Integrative health practitioners',
            'goals': 'Promote wellness packages and holistic beauty, educate clients on long-term results, build steady digital leads',
            'pain_points': 'Hard to communicate full service scope online, weak online presence or content marketing strategy',
            'key_message': 'Position your wellness brand as the trusted destination for health and beauty transformation.',
            'message_tone': 'Holistic, educational'
        },
        {
            'name': 'Aesthetic Clinic',
            'description': 'General Cosmetic Practice',
            'age_range': '30-65',
            'gender_distribution': 'Mixed',
            'goals': 'Increase patient bookings, improve brand visibility, generate consistent leads',
            'pain_points': 'Competition with specialized practices, difficulty differentiating services, inconsistent lead flow',
            'key_message': 'Grow your aesthetic practice with comprehensive digital marketing strategies.',
            'message_tone': 'Professional, growth-focused'
        }
    ]
    
    for persona_data in personas:
        try:
            db_manager.create_persona(**persona_data)
            print(f"  ✅ Created persona: {persona_data['name']}")
        except Exception as e:
            print(f"  ⚠️  Persona '{persona_data['name']}' may already exist: {str(e)}")
    
    print("✅ Persona seeding complete!")


def reset_database():
    """Drop and recreate all tables (CAUTION: This deletes all data!)"""
    print("\n⚠️  WARNING: This will delete ALL data!")
    confirmation = input("Type 'YES' to continue: ")
    
    if confirmation == 'YES':
        print("\n🗑️  Dropping all tables...")
        db_manager.drop_tables()
        print("✅ Tables dropped!")
        
        print("\n🔧 Recreating tables...")
        init_database()
    else:
        print("❌ Reset cancelled.")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize the database')
    parser.add_argument('--reset', action='store_true', help='Reset database (deletes all data)')
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database()