import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.linkedin_scraper import LinkedInScraper
import os
from dotenv import load_dotenv

load_dotenv()

email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')

scraper = LinkedInScraper(email, password, headless=False)
scraper.setup_driver()

# Manual login check
print("Opening LinkedIn login page...")
scraper.driver.get('https://www.linkedin.com/login')
print("Please login manually in the browser window")
print("Press Enter here AFTER you've logged in and see your feed...")
input()

print("Testing search...")
scraper.driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
time.sleep(3)

from selenium.webdriver.common.by import By
results = scraper.driver.find_elements(By.CSS_SELECTOR, 'div.b9fd59a4')
print(f"Found {len(results)} cards")

# Filter for real person cards
valid = []
for card in results:
    try:
        link = card.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
        href = link.get_attribute('href')
        if '/in/' in href and 'linkedin.com/in/' in href:
            valid.append(card)
            name = link.text.strip()
            print(f"✅ Found: {name} - {href[:50]}")
    except:
        pass

print(f"\nTotal valid person cards: {len(valid)}")
input("Press Enter to close...")
scraper.close()
