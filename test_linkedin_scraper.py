# scripts/test_linkedin_scraper.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.linkedin_scraper import LinkedInScraper
import os
from dotenv import load_dotenv

load_dotenv()

def test_scraper():
    print("🧪 Testing LinkedIn Scraper...")
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if not email or not password:
        print("❌ Missing LinkedIn credentials in .env")
        return False
    
    try:
        # Test with visible browser to see what's happening
        scraper = LinkedInScraper(email, password, headless=False)
        
        print("1️⃣ Setting up driver...")
        scraper.setup_driver()
        
        print("2️⃣ Attempting login...")
        login_success = scraper.login()
        
        if not login_success:
            print("❌ Login failed!")
            input("Press Enter to close browser...")
            scraper.close()
            return False
        
        print("✅ Login successful!")
        
        print("3️⃣ Testing search...")
        # Simple test search
        scraper.driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
        
        input("Press Enter to close browser (check if search worked)...")
        scraper.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_scraper()