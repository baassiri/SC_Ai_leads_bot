"""
Find the REAL result card container
"""
import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

load_dotenv()

def find_real_containers():
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Login
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(5)
        
        # Search
        driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
        time.sleep(3)
        
        print("🔍 Strategy: Find containers that have BOTH a profile link AND text")
        print("="*60)
        
        # Find all profile links
        all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
        print(f"Found {len(all_links)} total profile links")
        
        # For each link, go up the DOM to find the card container
        containers = {}
        
        for link in all_links[:20]:  # Check first 20 links
            try:
                href = link.get_attribute('href')
                if not href or 'linkedin.com/in/' not in href:
                    continue
                
                # Walk up the DOM tree
                current = link
                for level in range(1, 10):
                    current = current.find_element(By.XPATH, '..')
                    
                    # Check if this element has substantial text
                    text = current.text.strip()
                    
                    if len(text) > 50 and '\n' in text:  # Has multi-line text
                        # This might be our card!
                        tag = current.tag_name
                        classes = current.get_attribute('class')
                        
                        if classes:
                            first_class = classes.split()[0] if classes.split() else ''
                            
                            if first_class not in containers:
                                containers[first_class] = []
                            
                            containers[first_class].append({
                                'tag': tag,
                                'text_length': len(text),
                                'has_profile_link': True
                            })
                        break
            except:
                continue
        
        print(f"\n✅ Found {len(containers)} unique container classes:")
        
        for cls, items in sorted(containers.items(), key=lambda x: len(x[1]), reverse=True):
            count = len(items)
            if count >= 5 and count <= 20:  # Likely the results
                print(f"\n🎯 WINNER: '.{cls}' ({count} containers)")
                print(f"   Tag: {items[0]['tag']}")
                print(f"   Average text length: {sum(i['text_length'] for i in items) // len(items)}")
                
                # Test this selector
                test_elements = driver.find_elements(By.CSS_SELECTOR, f'.{cls}')
                print(f"   ✅ Selector finds {len(test_elements)} elements")
                
                if test_elements:
                    first = test_elements[0]
                    print(f"\n   📋 First result preview:")
                    text_lines = first.text.strip().split('\n')[:3]
                    for line in text_lines:
                        print(f"      {line[:60]}")
        
        input("\nPress Enter to close...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    find_real_containers()
