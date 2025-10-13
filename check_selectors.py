# Open the scraper and show the selectors being used
with open('backend/scrapers/linkedin_scraper.py', 'r') as f:
    content = f.read()
    
# Find the selector lines
import re
selectors = re.findall(r"\.CSS_SELECTOR,\s*['\"]([^'\"]+)['\"]", content)

print("Current CSS Selectors:")
for i, sel in enumerate(selectors, 1):
    print(f"{i}. {sel}")