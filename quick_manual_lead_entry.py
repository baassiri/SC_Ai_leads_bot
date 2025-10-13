"""
Quick Manual Lead Entry - FIXED VERSION
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_manager import db_manager

def add_test_leads():
    print("="*60)
    print("Manual Lead Entry for Testing")
    print("="*60)
    print("\nThis will add 5 test leads to your database")
    print("You can then:")
    print("  1. Generate A/B/C message variants")
    print("  2. Test manual sending")
    print("  3. Track performance\n")
    
    input("Press Enter to add test leads...")
    
    test_leads = [
        {
            'name': 'Sarah Johnson',
            'title': 'Marketing Director',
            'company': 'TechCorp Inc',
            'location': 'San Francisco, CA',
            'headline': 'Driving growth through digital marketing',
            'profile_url': 'https://linkedin.com/in/sarah-johnson-test'
        },
        {
            'name': 'Michael Chen',
            'title': 'Agency Owner',
            'company': 'Creative Solutions',
            'location': 'New York, NY',
            'headline': 'Helping businesses scale with automation',
            'profile_url': 'https://linkedin.com/in/michael-chen-test'
        },
        {
            'name': 'Emily Rodriguez',
            'title': 'CEO',
            'company': 'StartupXYZ',
            'location': 'Austin, TX',
            'headline': 'Building the future of eCommerce',
            'profile_url': 'https://linkedin.com/in/emily-rodriguez-test'
        },
        {
            'name': 'David Park',
            'title': 'CMO',
            'company': 'Growth Marketing Co',
            'location': 'Los Angeles, CA',
            'headline': 'Data-driven marketing strategist',
            'profile_url': 'https://linkedin.com/in/david-park-test'
        },
        {
            'name': 'Jennifer Williams',
            'title': 'Operations Manager',
            'company': 'Automation Hub',
            'location': 'Seattle, WA',
            'headline': 'Streamlining business operations',
            'profile_url': 'https://linkedin.com/in/jennifer-williams-test'
        }
    ]
    
    added = 0
    for lead in test_leads:
        try:
            # Create lead WITHOUT ai_score (it's set by AI scoring later)
            lead_id = db_manager.create_lead(
                name=lead['name'],
                profile_url=lead['profile_url'],
                title=lead['title'],
                company=lead['company'],
                location=lead['location'],
                headline=lead['headline'],
                industry='Technology'
            )
            
            # Now update the lead with a high score for testing
            if lead_id:
                with db_manager.session_scope() as session:
                    from backend.database.models import Lead
                    db_lead = session.query(Lead).filter(Lead.id == lead_id).first()
                    if db_lead:
                        db_lead.ai_score = 85  # Set high score for testing
                        print(f"✅ Added: {lead['name']} - {lead['title']} (Score: 85)")
                        added += 1
        except Exception as e:
            print(f"❌ Failed to add {lead['name']}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Successfully added {added} test leads!")
    print("\nNext steps:")
    print("1. Go to http://localhost:5000/leads")
    print("2. Select the leads")
    print("3. Click 'Generate Messages'")
    print("4. Review A/B/C variants")

if __name__ == '__main__':
    add_test_leads()