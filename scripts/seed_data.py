"""
SC AI Lead Generation System - Dynamic Seed Data Script
Populate database with sample leads based on UPLOADED personas
Now supports any persona document you upload!
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.database.models import Base


def generate_sample_lead_for_persona(persona):
    """Generate a realistic sample lead based on a persona"""
    
    # Extract persona characteristics
    persona_name = persona.get('name', 'Professional').lower()
    
    # Dynamic name generation
    first_names = ['John', 'Sarah', 'Michael', 'Jessica', 'David', 'Emily', 'Robert', 'Lisa', 
                   'James', 'Amanda', 'Daniel', 'Maria', 'Chris', 'Jennifer', 'Ryan', 'Nicole']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson']
    
    # Dynamic title generation based on persona keywords
    if any(word in persona_name for word in ['founder', 'entrepreneur', 'owner', 'ceo']):
        titles = ['Founder & CEO', 'Co-Founder', 'Entrepreneur', 'Business Owner', 'Managing Director']
    elif any(word in persona_name for word in ['marketing', 'agency', 'digital']):
        titles = ['Marketing Director', 'Agency Owner', 'Digital Marketing Manager', 'CMO', 'Creative Director']
    elif any(word in persona_name for word in ['tech', 'software', 'developer', 'engineer']):
        titles = ['CTO', 'Tech Lead', 'Software Engineer', 'Product Manager', 'VP of Engineering']
    elif any(word in persona_name for word in ['sales', 'growth', 'revenue']):
        titles = ['VP of Sales', 'Sales Director', 'Growth Manager', 'Business Development Lead']
    elif any(word in persona_name for word in ['consultant', 'advisor', 'coach']):
        titles = ['Business Consultant', 'Strategy Advisor', 'Executive Coach', 'Principal Consultant']
    elif any(word in persona_name for word in ['ecommerce', 'commerce', 'retail', 'store']):
        titles = ['E-commerce Director', 'Online Store Owner', 'Retail Manager', 'Commerce Lead']
    elif any(word in persona_name for word in ['service', 'saas', 'software']):
        titles = ['Service Manager', 'SaaS Founder', 'Operations Director', 'Customer Success Lead']
    else:
        titles = ['Director', 'Manager', 'Executive', 'VP', 'Business Leader']
    
    # Dynamic company generation based on persona
    if any(word in persona_name for word in ['agency', 'marketing', 'creative']):
        company_types = ['Digital Agency', 'Marketing Co', 'Creative Studios', 'Brand Agency', 'Media Group']
    elif any(word in persona_name for word in ['tech', 'software', 'startup']):
        company_types = ['Tech Solutions', 'Software Labs', 'Innovation Hub', 'Tech Ventures', 'Digital Platform']
    elif any(word in persona_name for word in ['ecommerce', 'retail', 'store']):
        company_types = ['Online Store', 'E-commerce Co', 'Retail Group', 'Digital Marketplace', 'Commerce Platform']
    elif any(word in persona_name for word in ['consultant', 'advisor']):
        company_types = ['Consulting Group', 'Advisory Partners', 'Strategy Firm', 'Business Consultants']
    elif any(word in persona_name for word in ['service', 'saas']):
        company_types = ['Service Company', 'SaaS Platform', 'Business Services', 'Solutions Provider']
    else:
        company_types = ['Enterprises', 'Group', 'LLC', 'Corporation', 'Partners']
    
    company_prefixes = ['Prime', 'Elite', 'Next', 'Pro', 'Bright', 'Smart', 'Peak', 'Summit', 'Core', 'Future']
    
    # Generate lead data
    first = random.choice(first_names)
    last = random.choice(last_names)
    name = f"{first} {last}"
    title = random.choice(titles)
    company = f"{random.choice(company_prefixes)} {random.choice(company_types)}"
    
    # Dynamic industry based on persona
    if any(word in persona_name for word in ['tech', 'software']):
        industry = 'Technology'
    elif any(word in persona_name for word in ['marketing', 'agency']):
        industry = 'Marketing & Advertising'
    elif any(word in persona_name for word in ['ecommerce', 'retail']):
        industry = 'E-commerce & Retail'
    elif any(word in persona_name for word in ['consultant', 'coach']):
        industry = 'Professional Services'
    else:
        industry = 'Business Services'
    
    locations = ['New York, NY', 'San Francisco, CA', 'Austin, TX', 'Chicago, IL', 'Boston, MA',
                 'Seattle, WA', 'Denver, CO', 'Atlanta, GA', 'Miami, FL', 'Portland, OR']
    
    company_sizes = ['1-10 employees', '11-50 employees', '51-200 employees', '201-500 employees']
    
    # Create headline from persona description or goals
    persona_desc = persona.get('description', '')
    if persona_desc:
        headline = f"{title} | {persona_desc}"
    else:
        headline = f"{title} | Growing {company}"
    
    # Create summary from persona goals
    goals = persona.get('goals', '')
    if goals:
        goal_lines = [g.strip() for g in goals.split('\n') if g.strip() and not g.strip().startswith('•')]
        summary = f"Focused on {goal_lines[0] if goal_lines else 'business growth'}. {random.randint(5, 20)}+ years experience in {industry.lower()}."
    else:
        summary = f"Experienced {title.lower()} focused on growth and innovation. {random.randint(5, 20)}+ years in {industry.lower()}."
    
    return {
        'name': name,
        'title': title,
        'company': company,
        'industry': industry,
        'location': random.choice(locations),
        'profile_url': f'https://linkedin.com/in/{first.lower()}-{last.lower()}',
        'headline': headline[:200],  # LinkedIn headline limit
        'summary': summary[:500],  # Keep it concise
        'company_size': random.choice(company_sizes),
        'ai_score': random.randint(70, 98),  # High quality leads
        'status': random.choice(['new', 'new', 'new', 'contacted', 'replied'])  # Mostly new
    }


def seed_dynamic_leads(num_leads_per_persona=2):
    """Seed sample leads based on personas in database"""
    print("\n💥 Seeding Dynamic Sample Leads...")
    
    # Get all personas from database
    personas = db_manager.get_all_personas()
    
    if not personas:
        print("  ⚠️  No personas found in database!")
        print("  📋 Please upload a persona document first via the UI")
        return []
    
    print(f"  📊 Found {len(personas)} personas in database")
    print(f"  🎯 Generating {num_leads_per_persona} sample leads per persona...")
    
    lead_ids = []
    
    for persona in personas:
        persona_name = persona.get('name', 'Unknown')
        print(f"\n  🎯 Generating leads for: {persona_name}")
        
        for i in range(num_leads_per_persona):
            try:
                # Generate lead based on this persona
                lead_data = generate_sample_lead_for_persona(persona)
                
                # Create lead in database
                lead_id = db_manager.create_lead(
                    name=lead_data['name'],
                    profile_url=lead_data['profile_url'],
                    title=lead_data['title'],
                    company=lead_data['company'],
                    industry=lead_data['industry'],
                    location=lead_data['location'],
                    headline=lead_data['headline'],
                    summary=lead_data['summary'],
                    company_size=lead_data['company_size']
                )
                
                if lead_id:
                    # Update with AI score and persona
                    db_manager.update_lead_score(
                        lead_id,
                        ai_score=lead_data['ai_score'],
                        persona_id=persona.get('id'),
                        score_reasoning=f"High match for {persona_name} persona"
                    )
                    
                    # Update status
                    db_manager.update_lead_status(lead_id, status=lead_data['status'])
                    
                    lead_ids.append(lead_id)
                    print(f"    ✅ {lead_data['name']} - {lead_data['title']} (Score: {lead_data['ai_score']})")
                
            except Exception as e:
                print(f"    ⚠️  Error creating lead: {str(e)}")
    
    return lead_ids


def seed_activity_logs():
    """Seed some activity logs for demonstration"""
    print("\n📋 Seeding Activity Logs...")
    
    activities = [
        {
            'activity_type': 'file_upload',
            'description': 'AI analyzed uploaded persona document',
            'status': 'success'
        },
        {
            'activity_type': 'scrape',
            'description': 'Sample leads generated based on personas',
            'status': 'success'
        },
        {
            'activity_type': 'score',
            'description': 'AI scored sample leads with persona matching',
            'status': 'success'
        }
    ]
    
    for activity in activities:
        try:
            db_manager.log_activity(**activity)
            print(f"  ✅ Logged: {activity['description']}")
        except Exception as e:
            print(f"  ⚠️  Error logging activity: {str(e)}")


def main():
    """Main seeding function - now dynamic!"""
    print("=" * 60)
    print("🌱 SC AI Lead Generation System - Dynamic Database Seeding")
    print("=" * 60)
    print("\n✨ This script now uses YOUR uploaded personas!")
    print("   No more hardcoded medical leads - everything is dynamic!\n")
    
    try:
        # Initialize database tables
        print("🔧 Creating database tables...")
        db_manager.create_tables()
        
        # Check for personas
        personas = db_manager.get_all_personas()
        
        if not personas:
            print("\n" + "=" * 60)
            print("⚠️  NO PERSONAS FOUND")
            print("=" * 60)
            print("\n📋 Please follow these steps:")
            print("  1. Run: python backend/app.py")
            print("  2. Visit: http://localhost:5000/dashboard")
            print("  3. Upload your persona document (Word, PDF, etc.)")
            print("  4. Run this script again to generate sample leads")
            print("\n" + "=" * 60)
            return
        
        # Seed dynamic leads based on uploaded personas
        lead_ids = seed_dynamic_leads(num_leads_per_persona=2)
        
        # Seed activity logs
        seed_activity_logs()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Dynamic Database Seeding Complete!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  • Personas found: {len(personas)}")
        print(f"  • Sample leads created: {len(lead_ids)}")
        print(f"  • All leads match YOUR personas!")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Visit: http://localhost:5000/leads")
        print(f"  2. See leads matching your personas!")
        print(f"  3. Run the bot to generate more real leads")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()