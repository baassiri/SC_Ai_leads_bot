"""
SC AI Lead Generation System - Seed Data Script
Populate database with sample personas and leads for testing
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.database.models import Base


def seed_personas():
    """Seed persona data from Targets.docx analysis"""
    print("\n🎯 Seeding Personas...")
    
    personas = [
        {
            'name': 'Plastic Surgeon',
            'description': 'The Prestige Provider',
            'age_range': '40-65',
            'gender_distribution': 'Predominantly male (70-80%)',
            'goals': '''
• Attract high-value cosmetic cases (rhinoplasty, facelifts, breast augmentation)
• Build strong regional reputation as "go-to" surgeon
• Fill schedule with elective procedures (higher margins)
• Reduce dependence on insurance/reconstruction work
            '''.strip(),
            'pain_points': '''
• Competing with med-spas offering cheaper non-surgical treatments
• Inconsistent patient flow month-to-month
• Website doesn't reflect premium brand positioning
• Difficulty standing out in saturated market
• Low conversion from consult to booking
            '''.strip(),
            'key_message': 'Grow your reputation and patient bookings with proven digital systems built specifically for plastic surgeons.',
            'message_tone': 'Consultative, prestige-focused, data-driven'
        },
        {
            'name': 'Dermatologist',
            'description': 'The Clinical Authority',
            'age_range': '35-60',
            'gender_distribution': 'Mix of male/female (60/40)',
            'goals': '''
• Balance medical dermatology with aesthetic revenue
• Increase bookings for injectables, lasers, and cosmetic procedures
• Enhance online visibility and Google ranking
• Build authority as local skin care expert
            '''.strip(),
            'pain_points': '''
• Limited time for marketing while managing medical practice
• Weak online reviews or local SEO presence
• Not converting enough cosmetic consults
• Competing with med-spas and nurse injectors
            '''.strip(),
            'key_message': 'Expand your aesthetic revenue with results-driven marketing systems designed for dermatology practices.',
            'message_tone': 'Clinical authority, results-oriented, professional'
        },
        {
            'name': 'Med Spa Owner',
            'description': 'The Growth Seeker',
            'age_range': '30-55',
            'gender_distribution': 'Often female entrepreneurs (65%)',
            'goals': '''
• Consistent monthly bookings for injectables and body treatments
• Scale brand awareness in local market
• Automate client retention and repeat bookings
• Stand out from 10+ competitors in same zip code
            '''.strip(),
            'pain_points': '''
• High local competition from other med-spas
• Poor ad performance or can't track ROI
• Weak branding or inconsistent visual identity
• Difficulty getting repeat clients
• Cash flow unpredictability
            '''.strip(),
            'key_message': 'Dominate your local market with data-backed campaigns that turn browsers into loyal med-spa clients.',
            'message_tone': 'Growth-oriented, entrepreneurial, data-backed'
        },
        {
            'name': 'Day Spa',
            'description': 'The Relaxation Brand Builder',
            'age_range': '35-60',
            'gender_distribution': 'Mostly female ownership (75%)',
            'goals': '''
• Attract consistent appointments for facials, massages, and wellness
• Improve Google Maps and social media visibility
• Retain clients through memberships and packages
• Build recognizable local brand
            '''.strip(),
            'pain_points': '''
• Low repeat-visit rates (one-time clients)
• Inconsistent messaging across platforms
• Outdated website that doesn't convert
• Competing with franchise spas (Massage Envy, etc.)
            '''.strip(),
            'key_message': 'Build a recognizable, trusted spa brand with targeted marketing and retention systems.',
            'message_tone': 'Brand-building, retention-focused, wellness-oriented'
        },
        {
            'name': 'Wellness Center',
            'description': 'The Holistic Healer',
            'age_range': '30-60',
            'gender_distribution': 'Integrative health practitioners (mix)',
            'goals': '''
• Promote wellness packages combining multiple services
• Educate clients on long-term health and beauty benefits
• Build steady stream of digital leads
• Position as trusted holistic health destination
            '''.strip(),
            'pain_points': '''
• Hard to communicate full scope of services online
• Weak SEO or content marketing strategy
• Difficulty differentiating from traditional spas
• Need to educate market on holistic approach
            '''.strip(),
            'key_message': 'Position your wellness brand as the trusted destination for holistic health and beauty transformation.',
            'message_tone': 'Holistic, educational, long-term focused'
        },
        {
            'name': 'Aesthetic Clinic',
            'description': 'General Cosmetic Practice',
            'age_range': '30-65',
            'gender_distribution': 'Mixed (50/50)',
            'goals': '''
• Increase patient bookings across all services
• Improve brand visibility in competitive market
• Generate consistent qualified leads
• Build strong online reputation
            '''.strip(),
            'pain_points': '''
• Competition with specialized practices
• Difficulty differentiating services and expertise
• Inconsistent lead flow month-to-month
• Weak online presence or outdated marketing
            '''.strip(),
            'key_message': 'Grow your aesthetic practice with comprehensive digital marketing strategies that deliver results.',
            'message_tone': 'Professional, growth-focused, comprehensive'
        }
    ]
    
    persona_ids = {}
    for persona_data in personas:
        try:
            persona_id = db_manager.create_persona(**persona_data)
            persona_ids[persona_data['name']] = persona_id
            print(f"  ✅ Created persona: {persona_data['name']}")
        except Exception as e:
            print(f"  ⚠️ Persona '{persona_data['name']}' may already exist: {str(e)}")
    
    return persona_ids


def seed_leads(persona_ids):
    """Seed sample lead data"""
    print("\n👥 Seeding Sample Leads...")
    
    # Sample lead data with realistic profiles
    sample_leads = [
        {
            'name': 'Dr. Sarah Johnson',
            'title': 'Board-Certified Plastic Surgeon',
            'company': 'Beverly Hills Aesthetics',
            'industry': 'Medical Practice',
            'location': 'Los Angeles, CA',
            'profile_url': 'https://www.linkedin.com/in/sarah-johnson-plasticsurgeon/',
            'headline': 'Board-Certified Plastic Surgeon | Specializing in Facial Aesthetics & Body Contouring',
            'summary': '15+ years experience in cosmetic surgery. Featured in Vogue and Harper\'s Bazaar.',
            'company_size': '11-50 employees',
            'ai_score': 92,
            'persona_name': 'Plastic Surgeon',
            'status': 'new'
        },
        {
            'name': 'Dr. Michael Chen',
            'title': 'Dermatologist & Medical Director',
            'company': 'Skin Perfect Dermatology',
            'industry': 'Medical Practice',
            'location': 'New York, NY',
            'profile_url': 'https://www.linkedin.com/in/michael-chen-dermatologist/',
            'headline': 'Board-Certified Dermatologist | Laser & Injectable Specialist',
            'summary': 'Medical and cosmetic dermatology. Expert in laser treatments and injectables.',
            'company_size': '11-50 employees',
            'ai_score': 87,
            'persona_name': 'Dermatologist',
            'status': 'contacted'
        },
        {
            'name': 'Jessica Williams',
            'title': 'Aesthetic Nurse Practitioner',
            'company': 'Glow Med Spa',
            'industry': 'Medical Practice',
            'location': 'Miami, FL',
            'profile_url': 'https://www.linkedin.com/in/jessica-williams-np/',
            'headline': 'Aesthetic NP | Expert in Injectables & Skin Rejuvenation',
            'summary': 'Certified in advanced injection techniques. Passion for natural-looking results.',
            'company_size': '1-10 employees',
            'ai_score': 76,
            'persona_name': 'Med Spa Owner',
            'status': 'new'
        },
        {
            'name': 'Amanda Rodriguez',
            'title': 'Owner & Medical Director',
            'company': 'Luminous Aesthetics',
            'industry': 'Medical Practice',
            'location': 'Houston, TX',
            'profile_url': 'https://www.linkedin.com/in/amanda-rodriguez-medspa/',
            'headline': 'Med Spa Owner | Building the Future of Aesthetic Medicine',
            'summary': 'Entrepreneur building a chain of luxury med spas across Texas.',
            'company_size': '11-50 employees',
            'ai_score': 94,
            'persona_name': 'Med Spa Owner',
            'status': 'replied'
        },
        {
            'name': 'Dr. Robert Kim',
            'title': 'Plastic & Reconstructive Surgeon',
            'company': 'Windy City Plastic Surgery',
            'industry': 'Medical Practice',
            'location': 'Chicago, IL',
            'profile_url': 'https://www.linkedin.com/in/robert-kim-surgeon/',
            'headline': 'Board-Certified Plastic Surgeon | 15+ Years Experience',
            'summary': 'Specializing in breast augmentation, rhinoplasty, and body contouring.',
            'company_size': '11-50 employees',
            'ai_score': 68,
            'persona_name': 'Plastic Surgeon',
            'status': 'archived'
        },
        {
            'name': 'Dr. Emily Martinez',
            'title': 'Dermatologist',
            'company': 'Clear Skin Dermatology',
            'industry': 'Medical Practice',
            'location': 'Phoenix, AZ',
            'profile_url': 'https://www.linkedin.com/in/emily-martinez-derm/',
            'headline': 'Dermatologist | Acne & Anti-Aging Specialist',
            'summary': 'Helping patients achieve healthy, beautiful skin through medical and cosmetic treatments.',
            'company_size': '1-10 employees',
            'ai_score': 81,
            'persona_name': 'Dermatologist',
            'status': 'new'
        },
        {
            'name': 'Sophia Patel',
            'title': 'Founder & CEO',
            'company': 'Radiance Med Spa',
            'industry': 'Medical Practice',
            'location': 'San Francisco, CA',
            'profile_url': 'https://www.linkedin.com/in/sophia-patel-medspa/',
            'headline': 'Med Spa Entrepreneur | Laser & Body Contouring Expert',
            'summary': 'Built 3 successful med spas from scratch. Featured in Forbes 30 Under 30.',
            'company_size': '51-200 employees',
            'ai_score': 96,
            'persona_name': 'Med Spa Owner',
            'status': 'contacted'
        },
        {
            'name': 'Dr. James Anderson',
            'title': 'Cosmetic Surgeon',
            'company': 'Anderson Aesthetics',
            'industry': 'Medical Practice',
            'location': 'Dallas, TX',
            'profile_url': 'https://www.linkedin.com/in/james-anderson-cosmetic/',
            'headline': 'Double Board-Certified Surgeon | Mommy Makeover Specialist',
            'summary': '20+ years experience. Known for natural, beautiful results.',
            'company_size': '11-50 employees',
            'ai_score': 89,
            'persona_name': 'Plastic Surgeon',
            'status': 'new'
        },
        {
            'name': 'Lisa Thompson',
            'title': 'Spa Owner & Wellness Coach',
            'company': 'Serenity Day Spa',
            'industry': 'Wellness & Spa',
            'location': 'Seattle, WA',
            'profile_url': 'https://www.linkedin.com/in/lisa-thompson-spa/',
            'headline': 'Day Spa Owner | Creating Relaxation & Rejuvenation Experiences',
            'summary': 'Holistic approach to beauty and wellness. 10+ years in spa industry.',
            'company_size': '1-10 employees',
            'ai_score': 72,
            'persona_name': 'Day Spa',
            'status': 'new'
        },
        {
            'name': 'Dr. David Lee',
            'title': 'Medical Director',
            'company': 'Elite Aesthetic Clinic',
            'industry': 'Medical Practice',
            'location': 'Boston, MA',
            'profile_url': 'https://www.linkedin.com/in/david-lee-aesthetics/',
            'headline': 'Aesthetic Medicine Expert | Injectables & Non-Surgical Treatments',
            'summary': 'Pioneering advanced aesthetic treatments. Published researcher.',
            'company_size': '11-50 employees',
            'ai_score': 85,
            'persona_name': 'Aesthetic Clinic',
            'status': 'contacted'
        },
        {
            'name': 'Maria Garcia',
            'title': 'Holistic Health Practitioner',
            'company': 'Wellness & Beauty Center',
            'industry': 'Wellness & Spa',
            'location': 'Portland, OR',
            'profile_url': 'https://www.linkedin.com/in/maria-garcia-wellness/',
            'headline': 'Holistic Wellness Expert | Integrative Beauty & Health',
            'summary': 'Combining Eastern and Western approaches to wellness and beauty.',
            'company_size': '1-10 employees',
            'ai_score': 70,
            'persona_name': 'Wellness Center',
            'status': 'new'
        },
        {
            'name': 'Dr. Rachel Green',
            'title': 'Dermatology & Aesthetics',
            'company': 'Green Dermatology',
            'industry': 'Medical Practice',
            'location': 'Austin, TX',
            'profile_url': 'https://www.linkedin.com/in/rachel-green-derm/',
            'headline': 'Board-Certified Dermatologist | Botox & Filler Specialist',
            'summary': 'Passionate about helping patients look and feel their best.',
            'company_size': '11-50 employees',
            'ai_score': 83,
            'persona_name': 'Dermatologist',
            'status': 'new'
        },
        {
            'name': 'Nicole Brown',
            'title': 'Med Spa Director',
            'company': 'Luxe Aesthetics',
            'industry': 'Medical Practice',
            'location': 'Las Vegas, NV',
            'profile_url': 'https://www.linkedin.com/in/nicole-brown-medspa/',
            'headline': 'Med Spa Professional | Body Sculpting & Skin Rejuvenation',
            'summary': 'Creating transformative experiences through advanced aesthetics.',
            'company_size': '11-50 employees',
            'ai_score': 79,
            'persona_name': 'Med Spa Owner',
            'status': 'contacted'
        },
        {
            'name': 'Dr. Christopher White',
            'title': 'Plastic Surgeon',
            'company': 'White Plastic Surgery',
            'industry': 'Medical Practice',
            'location': 'Atlanta, GA',
            'profile_url': 'https://www.linkedin.com/in/christopher-white-surgeon/',
            'headline': 'Board-Certified Plastic Surgeon | Breast & Body Specialist',
            'summary': 'Dedicated to natural-looking results and patient satisfaction.',
            'company_size': '1-10 employees',
            'ai_score': 77,
            'persona_name': 'Plastic Surgeon',
            'status': 'new'
        },
        {
            'name': 'Jennifer Taylor',
            'title': 'Spa & Wellness Director',
            'company': 'Tranquility Spa & Wellness',
            'industry': 'Wellness & Spa',
            'location': 'Denver, CO',
            'profile_url': 'https://www.linkedin.com/in/jennifer-taylor-spa/',
            'headline': 'Day Spa Owner | Massage, Facials & Holistic Treatments',
            'summary': 'Creating peaceful retreats for relaxation and rejuvenation.',
            'company_size': '1-10 employees',
            'ai_score': 65,
            'persona_name': 'Day Spa',
            'status': 'new'
        }
    ]
    
    lead_ids = []
    for lead_data in sample_leads:
        try:
            # Get persona ID
            persona_name = lead_data.pop('persona_name')
            persona_id = persona_ids.get(persona_name)
            
            # Set scraped timestamp
            days_ago = random.randint(1, 30)
            scraped_at = datetime.utcnow() - timedelta(days=days_ago)
            
            # Create lead
            lead_id = db_manager.create_lead(
                name=lead_data['name'],
                profile_url=lead_data['profile_url'],
                title=lead_data.get('title'),
                company=lead_data.get('company'),
                industry=lead_data.get('industry'),
                location=lead_data.get('location'),
                headline=lead_data.get('headline'),
                summary=lead_data.get('summary'),
                company_size=lead_data.get('company_size')
            )
            
            # Update with AI score and persona
            db_manager.update_lead_score(
                lead_id,
                ai_score=lead_data['ai_score'],
                persona_id=persona_id,
                score_reasoning=f"High match for {persona_name} persona based on title, company, and experience."
            )
            
            # Update status
            db_manager.update_lead_status(lead_id, status=lead_data['status'])
            
            lead_ids.append(lead_id)
            print(f"  ✅ Created lead: {lead_data['name']} (Score: {lead_data['ai_score']})")
            
        except Exception as e:
            print(f"  ⚠️ Error creating lead {lead_data['name']}: {str(e)}")
    
    return lead_ids


def seed_activity_logs():
    """Seed some activity logs for demonstration"""
    print("\n📋 Seeding Activity Logs...")
    
    activities = [
        {
            'activity_type': 'scrape',
            'description': 'Successfully scraped 15 leads from LinkedIn Sales Navigator',
            'status': 'success'
        },
        {
            'activity_type': 'score',
            'description': 'AI scored 15 leads with average score of 81.2',
            'status': 'success'
        },
        {
            'activity_type': 'message_generate',
            'description': 'Generated personalized messages for 5 high-value leads',
            'status': 'success'
        },
        {
            'activity_type': 'message_send',
            'description': 'Sent 3 connection requests to qualified leads',
            'status': 'success'
        },
        {
            'activity_type': 'credentials_saved',
            'description': 'User credentials updated successfully',
            'status': 'success'
        }
    ]
    
    for activity in activities:
        try:
            db_manager.log_activity(**activity)
            print(f"  ✅ Logged: {activity['description']}")
        except Exception as e:
            print(f"  ⚠️ Error logging activity: {str(e)}")


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 SC AI Lead Generation System - Database Seeding")
    print("=" * 60)
    
    try:
        # Initialize database tables
        print("\n🔧 Creating database tables...")
        db_manager.create_tables()
        
        # Seed personas
        persona_ids = seed_personas()
        
        # Seed leads
        lead_ids = seed_leads(persona_ids)
        
        # Seed activity logs
        seed_activity_logs()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Database Seeding Complete!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  • Personas created: {len(persona_ids)}")
        print(f"  • Leads created: {len(lead_ids)}")
        print(f"  • Activity logs: 5")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Run: python backend/app.py")
        print(f"  2. Visit: http://localhost:5000/dashboard")
        print(f"  3. Explore the dashboard with sample data!")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()