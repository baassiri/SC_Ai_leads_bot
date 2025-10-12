"""
Test LinkedIn Scraper - Find Aesthetic Professional Leads
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.scrapers.linkedin_scraper import LinkedInScraper

def main():
    print("🧪 TESTING LINKEDIN SCRAPER")
    
    linkedin_email = input("Enter LinkedIn email: ").strip()
    linkedin_password = input("Enter LinkedIn password: ").strip()
    
    print("\n1. Visible browser (recommended)")
    print("2. Headless mode")
    mode = input("Choose (1 or 2): ").strip()
    headless = (mode == "2")
    
    keywords = input("Search keywords (or press Enter for default): ").strip()
    if not keywords:
        keywords = "plastic surgeon dermatologist med spa owner"
    
    scraper = LinkedInScraper(
        email=linkedin_email,
        password=linkedin_password,
        headless=headless
    )
    
    filters = {'keywords': keywords}
    
    try:
        leads = scraper.scrape_leads(filters, max_pages=1)
        print(f"\n✅ Found {len(leads)} leads!")
        
        if leads:
            print("\nSample leads:")
            for i, lead in enumerate(leads[:3], 1):
                print(f"{i}. {lead['name']} - {lead.get('title', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()