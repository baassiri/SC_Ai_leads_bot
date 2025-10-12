from backend.ai_engine.message_generator import generate_connection_message
from backend.database.db_manager import db_manager

# Get a high-scoring lead
leads = db_manager.get_all_leads(min_score=70, limit=1)

if leads:
    lead = leads[0]
    
    # Generate message
    message = generate_connection_message(
        lead_name=lead['name'],
        lead_title=lead['title'],
        lead_company=lead['company'],
        persona_name="Marketing Agencies"  # or whatever persona
    )
    
    print(f"Generated message for {lead['name']}:")
    print(message)
else:
    print("No high-scoring leads found. Run scraper first!")