import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.credentials_manager import credentials_manager
from backend.database.db_manager import db_manager

print("Testing Backend Components...\n")

# Test 1: Credentials
try:
    creds = credentials_manager.get_linkedin_credentials()
    print(f"✅ LinkedIn: {creds['email']}" if creds else "❌ No LinkedIn credentials")
except:
    print("❌ Credentials error")

try:
    api_key = credentials_manager.get_openai_key()
    print(f"✅ OpenAI: {api_key[:10]}..." if api_key else "❌ No OpenAI key")
except:
    print("❌ OpenAI error")

# Test 2: Database
try:
    leads = db_manager.get_all_leads()
    messages = db_manager.get_all_messages()
    print(f"✅ Database: {len(leads)} leads, {len(messages)} messages")
except Exception as e:
    print(f"❌ Database: {e}")

# Test 3: Modules
try:
    from backend.automation.linkedin_message_sender import LinkedInMessageSender
    print("✅ LinkedIn sender OK")
except:
    print("❌ LinkedIn sender failed")

try:
    from backend.automation.scheduler import MessageScheduler
    print("✅ Scheduler OK")
except:
    print("❌ Scheduler failed")

try:
    from backend.automation.queue_processor import QueueProcessor
    print("✅ Queue processor OK")
except:
    print("❌ Queue processor failed")

print("\n✅ If all passed, continue to Flask tests")