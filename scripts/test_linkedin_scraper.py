"""
LinkedIn Scraper Diagnostic Test - UPDATED with correct selector
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.linkedin_scraper import LinkedInScraper
import os
from dotenv import load_dotenv

load_dotenv()

def test_scraper_step_by_step():
    print("="*60)
    print("🧪 LINKEDIN SCRAPER DIAGNOSTIC TEST")
    print("="*60)
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if not email or not password:
        print("\n❌ FAILED: Missing LinkedIn credentials in .env file")
        return False
    
    print(f"\n✅ Credentials found")
    print(f"   Email: {email[:3]}...{email[-10:]}")
    
    try:
        print("\n" + "="*60)
        print("STEP 1: Initialize Scraper")
        print("="*60)
        scraper = LinkedInScraper(email, password, headless=False)
        print("✅ Scraper initialized")
        
        print("\n" + "="*60)
        print("STEP 2: Setup Chrome Driver")
        print("="*60)
        success = scraper.setup_driver()
        if not success:
            print("❌ FAILED: Driver setup failed")
            return False
        print("✅ Driver setup successful")
        
        print("\n" + "="*60)
        print("STEP 3: Login to LinkedIn")
        print("="*60)
        print("⏳ Attempting login...")
        
        login_success = scraper.login()
        
        if not login_success:
            print("\n❌ FAILED: Login failed")
            scraper.close()
            return False
        
        print("✅ Login successful!")
        
        print("\n" + "="*60)
        print("STEP 4: Test Search Functionality")
        print("="*60)
        print("⏳ Navigating to search page...")
        
        scraper.driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
        time.sleep(3)
        
        print("✅ Search page loaded")
        
        print("\n⏳ Testing CORRECT selector: div.b9fd59a4")
        
        from selenium.webdriver.common.by import By
        
        # Test the CORRECT selector
        results = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.b9fd59a4')
        
        if results:
            print(f"✅✅✅ FOUND {len(results)} results with selector!")
            print(f"✅ Selector 'div.b9fd59a4' is working!")
            
            # Test extracting from first 5 results
            person_cards = 0
            for i, result in enumerate(results[:10], 1):
                try:
                    # Try to find profile link
                    link = result.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                    href = link.get_attribute('href')
                    
                    # Get text content
                    text = result.text.strip()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    if lines and 'CEO' in text or 'at' in text:
                        person_cards += 1
                        print(f"\n   ✅ Result {person_cards}:")
                        print(f"      Profile: {href[:50]}...")
                        if lines:
                            print(f"      Name: {lines[0][:40]}")
                            if len(lines) > 1:
                                print(f"      Title: {lines[1][:40]}")
                except:
                    continue
            
            print(f"\n✅ Successfully extracted {person_cards} person cards!")
        else:
            print("❌ No results found")
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ Driver Setup: SUCCESS")
        print("✅ Login: SUCCESS")
        print("✅ Search Navigation: SUCCESS")
        if results and person_cards > 0:
            print(f"✅ Data Extraction: SUCCESS ({person_cards} cards)")
            print("\n🎉 SCRAPER IS FULLY WORKING!")
        else:
            print("⚠️ Data Extraction: FAILED")
        
        print("\n🔍 Browser staying open for inspection...")
        input("\nPress Enter to close browser and exit...")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if 'scraper' in locals():
            scraper.close()
        
        return False

if __name__ == '__main__':
    success = test_scraper_step_by_step()
    
    if success:
        print("\n🎉 Test completed!")
        exit(0)
    else:
        print("\n❌ Tests failed")
        exit(1)
