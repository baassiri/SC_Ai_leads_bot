from backend.database.db_manager import db_manager

personas = db_manager.get_all_personas()

print("="*60)
print("Personas Extracted from Your Documents")
print("="*60)

for persona in personas:
    print(f"\n📋 {persona['name']}")
    print(f"   Keywords: {persona.get('message_tone', 'N/A')}")
    print(f"   Goals: {persona.get('goals', 'N/A')[:100]}...")
    print(f"   Pain Points: {persona.get('pain_points', 'N/A')[:100]}...")