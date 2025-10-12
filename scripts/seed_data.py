"""
SC AI Lead Generation System - Clean Dynamic Seed Data
Only generates sample leads from UPLOADED personas - no hardcoded data
"""

import sys
from pathlib import Path
from datetime import datetime
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager


def generate_sample_lead_for_persona(persona):
    """Generate a realistic sample lead based on a persona"""
    
    # Extract persona characteristics
    persona_name = persona.get('name', 'Professional').lower()
    
    # Dynamic name generation
    first_names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn']
    last_names = ['Chen', 'Patel', 'Kim', 'Martinez', 'Johnson', 'Williams', 'Lee', 'Garcia']
    
    # Dynamic title generation based on persona keywords
    job_titles = persona.get('job_titles', [])
    if job_titles:
        title = random.choice(job_titles)
    else:
        # Extract from name or use generic
        title = persona.get('name', 'Professional')
    
    # Dynamic company generation based on persona
    industries = persona.get('industries', ['Business Services'])
    industry = random.choice(industries) if industries else 'Business Services'
    
    # Generate company name
    company_prefixes = ['Global', 'Prime', 'Elite', 'Next', 'Pro', 'Bright', 'Smart', 'Peak']
    company_suffixes = ['Solutions', 'Group', 'Partners', 'Consulting', 'Agency', 'Labs', 'Inc']
    
    # Generate lead data
    first = random.choice(first_names)
    last = random.choice(last_names)
    name = f"{first} {last}"
    company = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}"
    
    locations = ['New York, NY', 'San Francisco, CA', 'Austin, TX', 'Chicago, IL', 'Boston, MA',
                 'Seattle, WA', 'Denver, CO', 'Atlanta, GA', 'Miami, FL', 'Portland, OR']
    
    company_sizes = ['1-10 employees', '11-50 employees', '51-200 employees', '201-500 employees']
    
    # Create headline from persona description
    persona_desc = persona.get('description', '')
    headline = f"{title} at {company}" + (f" | {persona_desc}" if persona_desc else "")
    
    # Create summary from persona goals
    goals = persona.get('goals', [])
    if goals and isinstance(goals, list):
        summary = f"Focused on {goals[0]}. Experienced professional in {industry.lower()}."
    else:
        summary = f"Experienced {title} focused on growth and innovation."
    
    return {
        'name': name,
        'title': title,
        'company': company,
        'industry': industry,
        'location': random.choice(locations),
        'profile_url': f'https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100, 999)}',
        'headline': headline[:200],
        'summary': summary[:500],
        'company_size': random.choice(company_sizes),
        'ai_score': random.randint(70, 98),
        'status': 'new'
    }


def seed_dynamic_leads(num_leads_per_persona=3):
    """Seed sample leads based on personas in database"""
    print("\n💥 Generating Sample Leads from Your Personas...")
    
    # Get all personas from database
    personas = db_manager.get_all_personas()
    
    if not personas:
        print("\n  ⚠️  No personas found!")
        print("  📋 Please upload a persona document first")
        return []
    
    print(f"  📊 Found {len(personas)} personas")
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
                    
                    lead_ids.append(lead_id)
                    print(f"    ✅ {lead_data['name']} - {lead_data['title']} (Score: {lead_data['ai_score']})")
                
            except Exception as e:
                print(f"    ⚠️  Error creating lead: {str(e)}")
    
    return lead_ids


def main():
    """Main seeding function"""
    print("=" * 60)
    print("🌱 Generating Sample Leads from Your Uploaded Personas")
    print("=" * 60)
    
    try:
        # Check for personas
        personas = db_manager.get_all_personas()
        
        if not personas:
            print("\n⚠️  NO PERSONAS FOUND")
            print("\nPlease:")
            print("  1. Run: python backend/app.py")
            print("  2. Visit: http://localhost:5000/dashboard")
            print("  3. Upload your persona document")
            print("  4. Run this script again")
            return
        
        # Generate sample leads
        lead_ids = seed_dynamic_leads(num_leads_per_persona=3)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Sample Leads Generated!")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"  • Personas: {len(personas)}")
        print(f"  • Sample leads: {len(lead_ids)}")
        print(f"\n🎯 Next: Visit http://localhost:5000/leads")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()