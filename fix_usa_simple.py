#!/usr/bin/env python3
"""
LinkedIn Scraper - USA Filter Fix ONLY
=======================================
Adds USA-only location filter to the scraper
"""

import sys
from pathlib import Path

print("=" * 70)
print("🇺🇸 ADDING USA-ONLY FILTER")
print("=" * 70)

scraper_file = Path("backend/scrapers/linkedin_scraper.py")

if not scraper_file.exists():
    print("\n❌ File not found!")
    sys.exit(1)

print("\n📂 Found scraper file!")

# Read file
with open(scraper_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the EXACT line
old_line = '            search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}"'
new_line = '            search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}&geoUrn=%5B%22103644278%22%5D"'

if old_line in content:
    content = content.replace(old_line, new_line)
    
    # Also add a print statement
    old_print = '            print(f"   Navigating to: {search_url}")'
    new_print = '            print(f"   Navigating to: {search_url}")\n            print("   🇺🇸 Location Filter: USA ONLY")'
    
    if old_print in content:
        content = content.replace(old_print, new_print)
    
    # Save
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ USA filter added successfully!")
    print("   🌎 Will only scrape United States leads")
else:
    print("⚠️ Could not find search URL line")
    print("\nPlease manually edit backend/scrapers/linkedin_scraper.py")
    print("Line 554: Add this to the end of the URL:")
    print("   &geoUrn=%5B%22103644278%22%5D")

print("\n" + "=" * 70)
print("✅ DONE! Now restart the server.")
print("=" * 70)
