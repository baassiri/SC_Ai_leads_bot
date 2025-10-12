"""
Quick Test Data Generator
Creates test personas, leads, and messages for testing
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.db_manager import db_manager

def create_test_data():
    """Create test data for testing messages functionality"""
    
    print("🎯 Creating test data...")
    
    # 1. Create test persona
    print("\n1. Creating test persona...")
    persona_id = db_manager.create_persona(
        name="VP of Marketing",
        description="Marketing executives at tech companies",
        goals="Increase lead generation and ROI",
        pain_points="Struggling with manual outreach",
        message_tone="Professional, value-focused"
    )
    print(f"   ✅ Created persona ID: {persona_id}")
    
    # 2. Create test leads
    print("\n2. Creating test leads...")
    leads_data = [
        {
            'name': 'John Smith',
            'title': 'VP of Marketing',
            'company': 'TechCorp',
            'profile_url': 'https://linkedin.com/in/johnsmith',
            'ai_score': 85
        },
        {
            'name': 'Sarah Johnson',
            'title': 'Marketing Director',
            'company': 'InnovateLabs',
            'profile_url': 'https://linkedin.com/in/sarahjohnson',
            'ai_score': 92
        },
        {
            'name': 'Michael Chen',
            'title': 'CMO',
            'company': 'GrowthCo',
            'profile_url': 'https://linkedin.com/in/michaelchen',
            'ai_score': 78
        }
    ]
    
    lead_ids = []
    for lead_data in leads_data:
        lead_id = db_manager.create_lead(
            name=lead_data['name'],
            profile_url=lead_data['profile_url'],
            title=lead_data['title'],
            company=lead_data['company'],
            industry='Technology',
            location='San Francisco, CA',
            headline=f"{lead_data['title']} at {lead_data['company']}"
        )
        
        # Update score
        db_manager.update_lead_score(
            lead_id,
            lead_data['ai_score'],
            persona_id=persona_id,
            score_reasoning=f"Strong match for {persona_id} persona"
        )
        
        lead_ids.append(lead_id)
        print(f"   ✅ Created lead: {lead_data['name']} (ID: {lead_id}, Score: {lead_data['ai_score']})")
    
    # 3. Create test messages
    print("\n3. Creating test messages...")
    message_variants = ['A', 'B', 'C']
    message_count = 0
    
    for lead_id, lead_data in zip(lead_ids, leads_data):
        for variant in message_variants:
            content = f"Hi {lead_data['name'].split()[0]},\n\nI help {lead_data['title']}s at companies like {lead_data['company']} improve their lead generation. Would you be open to a quick chat?\n\nBest,\nYour Name\n\n(Variant {variant})"
            
            # Create 2 drafts and 1 approved for first lead
            if lead_id == lead_ids[0]:
                if variant in ['A', 'B']:
                    status = 'draft'
                else:
                    status = 'approved'
            # All drafts for other leads
            else:
                status = 'draft'
            
            message_id = db_manager.create_message(
                lead_id=lead_id,
                message_type='connection_request',
                content=content,
                variant=variant,
                status=status,
                generated_by='test-script'
            )
            message_count += 1
            print(f"   ✅ Created message ID {message_id}: {lead_data['name']} - Variant {variant} ({status})")
    
    print(f"\n✅ Test data created successfully!")
    print(f"   • {len(lead_ids)} leads")
    print(f"   • {message_count} messages")
    
    # Show stats
    stats = db_manager.get_message_stats()
    print(f"\n📊 Message Stats:")
    print(f"   • Draft: {stats['draft']}")
    print(f"   • Approved: {stats['approved']}")
    print(f"   • Total: {stats['total']}")

if __name__ == '__main__':
    create_test_data()