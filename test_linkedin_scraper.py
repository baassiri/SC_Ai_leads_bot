"""
Test Regular LinkedIn Scraper
Run this after entering credentials in the UI
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.scrapers.linkedin_scraper import LinkedInScraper
from backend.credentials_manager import credentials_manager

def test_scraper():
    print("="*60)
    print("Testing Regular LinkedIn Scraper")
    print("="*60)
    
    # Get credentials from system
    creds = credentials_manager.get_linkedin_credentials()
    
    if not creds or not creds.get('email'):
        print("\n❌ No LinkedIn credentials found!")
        print("Please go to http://localhost:5000/ and save your credentials first")
        return
    
    email = creds['email']
    password = creds['password']
    
    print(f"\n✅ Using credentials for: {email}")
    print("\n⚠️  IMPORTANT:")
    print("- Browser will open (visible mode)")
    print("- Only scraping 10 leads max (safe)")
    print("- Using regular LinkedIn search")
    print("- Will take 2-3 minutes")
    
    input("\nPress Enter to start...")
    
    # Create scraper
    scraper = LinkedInScraper(
        email=email,
        password=password,
        headless=False,  # Keep visible so you can see
        sales_nav_preference=False  # Force regular LinkedIn
    )
    
    # Define search (use your persona keywords)
    filters = {
        'keywords': 'Marketing Director OR Agency Owner',
        'job_titles': ['Marketing Director', 'Agency Owner'],
        'locations': ['United States']
    }
    
    print("\n🚀 Starting scraper...")
    
    try:
        # Scrape leads (only 1 page = ~10 leads)
        leads = scraper.scrape_leads(filters, max_pages=1)
        
        if leads:
            print(f"\n✅ SUCCESS! Scraped {len(leads)} leads")
            print("\nFirst 3 leads:")
            for i, lead in enumerate(leads[:3], 1):
                print(f"\n{i}. {lead.get('name', 'Unknown')}")
                print(f"   Title: {lead.get('title', 'N/A')}")
                print(f"   Company: {lead.get('company', 'N/A')}")
                print(f"   Location: {lead.get('location', 'N/A')}")
        else:
            print("\n⚠️  No leads found - try different keywords")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close_session()
        print("\n✅ Browser closed")

if __name__ == '__main__':
    test_scraper()