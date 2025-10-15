"""
Enhanced LinkedIn Selector Finder
Checks profile links more thoroughly
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def find_linkedin_selectors(email, password, search_keywords="CEO founder"):
    print("=" * 70)
    print("ENHANCED LINKEDIN SELECTOR FINDER")
    print("=" * 70)
    
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    
    try:
        # Login
        print("\n[1] Logging in...")
        driver.get('https://www.linkedin.com/login')
        time.sleep(3)
        
        driver.find_element(By.CSS_SELECTOR, '#username').send_keys(email)
        driver.find_element(By.CSS_SELECTOR, '#password').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        print("   Waiting 10 seconds (solve CAPTCHA if needed)...")
        time.sleep(10)
        
        # Search
        print(f"\n[2] Searching for: {search_keywords}")
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_keywords.replace(' ', '%20')}"
        driver.get(search_url)
        time.sleep(5)
        
        print("\n[3] Finding ALL profile links on page...")
        print("-" * 70)
        
        # Find ALL profile links
        all_profile_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
        print(f"Found {len(all_profile_links)} total profile links on page")
        
        if len(all_profile_links) == 0:
            print("\n!!! NO PROFILE LINKS FOUND !!!")
            print("Are you sure the search loaded correctly?")
            print("Browser will stay open for 60 seconds - check manually")
            time.sleep(60)
            return
        
        # Show first few profile URLs
        print("\nFirst 5 profile links:")
        for i, link in enumerate(all_profile_links[:5]):
            href = link.get_attribute('href')
            text = link.text.strip()
            print(f"  [{i+1}] {text[:40]} -> {href[:60]}")
        
        # Find parent containers
        print("\n[4] Analyzing parent containers of profile links...")
        print("-" * 70)
        
        # Get first profile link and traverse up
        first_link = all_profile_links[0]
        
        print("\nTraversing up from first profile link...")
        current = first_link
        level = 0
        
        for i in range(10):  # Go up 10 levels
            try:
                parent = current.find_element(By.XPATH, '..')
                tag = parent.tag_name
                classes = parent.get_attribute('class')
                
                print(f"\nLevel {i+1} - <{tag}>")
                print(f"  Class: {classes}")
                
                # Check if this level contains multiple profile links
                links_in_parent = parent.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
                print(f"  Profile links in this element: {len(links_in_parent)}")
                
                # If parent has exactly 1 link, it's the card. If more, it's the list
                if len(links_in_parent) == 1:
                    print(f"  >>> THIS IS LIKELY THE CARD CONTAINER!")
                    card_selector = f"{tag}.{classes.split()[0]}" if classes else tag
                    print(f"  >>> Suggested selector: {card_selector}")
                
                current = parent
                
            except Exception as e:
                break
        
        # Try to find common parent
        print("\n[5] Looking for common container of all cards...")
        print("-" * 70)
        
        # Check if there's a UL/OL that contains most links
        for tag in ['ul', 'ol', 'div']:
            containers = driver.find_elements(By.TAG_NAME, tag)
            for container in containers:
                try:
                    links_in_container = container.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
                    
                    # If this container has most of the profile links, it's the results list
                    if len(links_in_container) >= len(all_profile_links) * 0.7:  # At least 70% of links
                        container_class = container.get_attribute('class')
                        print(f"\n>>> FOUND RESULTS CONTAINER!")
                        print(f"    Tag: <{tag}>")
                        print(f"    Class: {container_class}")
                        print(f"    Contains: {len(links_in_container)} profile links")
                        
                        # Find direct children
                        children = container.find_elements(By.XPATH, './*')
                        print(f"    Direct children: {len(children)}")
                        
                        if children:
                            first_child = children[0]
                            child_tag = first_child.tag_name
                            child_class = first_child.get_attribute('class')
                            print(f"\n    First child:")
                            print(f"      Tag: <{child_tag}>")
                            print(f"      Class: {child_class}")
                            print(f"      >>> CARD SELECTOR: {child_tag}.{child_class.split()[0]}")
                
                except Exception as e:
                    continue
        
        print("\n\n" + "=" * 70)
        print("SOLUTION:")
        print("=" * 70)
        print("\nUse the selectors marked with >>> above in your scraper")
        print("\nBrowser stays open for 60 seconds...")
        print("=" * 70)
        
        time.sleep(60)
        
    finally:
        driver.quit()
        print("\nDone!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("\nUsage: python enhanced_diagnose.py <email> <password> [keywords]")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    keywords = sys.argv[3] if len(sys.argv) > 3 else "CEO founder"
    
    find_linkedin_selectors(email, password, keywords)