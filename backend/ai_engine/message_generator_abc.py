"""
SC AI Lead Generation System - A/B/C Message Generator
✅ FIXED VERSION - Generates natural, human-sounding messages
"""

import sys
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager


class ABCMessageGenerator:
    """Generate A/B/C message variants for leads"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or credentials_manager.get_openai_key()
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"
    
    def generate_variants(self, lead: Dict) -> Dict[str, str]:
        """
        Generate 3 natural-sounding message variants (A, B, C) for a single lead
        
        Args:
            lead: Dict with lead information (name, title, company, persona)
            
        Returns:
            Dict with keys: variant_a, variant_b, variant_c
        """
        
        first_name = lead.get('name', '').split()[0] if lead.get('name') else 'there'
        title = lead.get('title', 'Professional')
        company = lead.get('company', 'your company')
        
        prompt = f"""You are writing LinkedIn connection requests. Write naturally like a real human, NOT like AI or a salesperson.

**Lead Info:**
- Name: {lead.get('name', 'Professional')}
- First Name: {first_name}
- Title: {title}
- Company: {company}

**CRITICAL RULES:**
1. Under 200 characters (LinkedIn connection request limit)
2. Sound like a REAL person texting a colleague
3. NO corporate buzzwords: "solutions", "value", "partnership", "synergy", "leverage"
4. NO AI phrases: "I noticed", "I came across", "I saw", "reaching out"
5. Be casual, direct, and friendly
6. Get to the point quickly
7. NO emojis
8. NO long introductions

**BAD Examples (DON'T write like this):**
❌ "Dear {first_name}, As the {title} of {company}, you're surely on the lookout for..."
❌ "Hi {first_name}, I noticed your impressive work at {company}. I'd love to discuss how our solutions..."
❌ "Hi {first_name}, I came across your profile and thought we could create synergy..."

**GOOD Examples (Write like THIS):**
✅ "Hey {first_name}, fellow {title} here - would love to connect and swap notes"
✅ "Hi {first_name}, I help {title}s with [specific problem]. Worth a quick chat?"
✅ "{first_name}, respect what you're building at {company}. Let's connect?"
✅ "Hey {first_name}, working on something for {title}s. Can I pick your brain?"

**Generate 3 DIFFERENT casual messages:**

VARIANT A - Direct approach (like a quick intro at a conference):


VARIANT B - Question-based (like asking for advice):


VARIANT C - Compliment-based (like genuine respect):

"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You write natural, human-sounding LinkedIn messages. No corporate speak. Be brief and casual like texting a friend."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,  # Higher for natural variation
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            variants = self._parse_variants(content)
            
            # Validate all variants exist
            required_keys = ['variant_a', 'variant_b', 'variant_c']
            for key in required_keys:
                if key not in variants or not variants[key]:
                    print(f"⚠️ Missing {key}, using fallback")
                    variants = self._get_fallback_variants(lead)
                    break
            
            return variants
            
        except Exception as e:
            print(f"❌ Error generating variants: {str(e)}")
            return self._get_fallback_variants(lead)
    
    def _parse_variants(self, content: str) -> Dict[str, str]:
        """Parse GPT-4 response into variant dictionary"""
        
        variants = {}
        lines = content.split('\n')
        current_variant = None
        current_message = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('VARIANT A'):
                if current_variant and current_message:
                    variants[current_variant] = ' '.join(current_message).strip()
                current_variant = 'variant_a'
                current_message = []
                # Check if message is on same line
                if ':' in line:
                    message_part = line.split(':', 1)[1].strip()
                    if message_part:
                        current_message.append(message_part)
            
            elif line.startswith('VARIANT B'):
                if current_variant and current_message:
                    variants[current_variant] = ' '.join(current_message).strip()
                current_variant = 'variant_b'
                current_message = []
                if ':' in line:
                    message_part = line.split(':', 1)[1].strip()
                    if message_part:
                        current_message.append(message_part)
            
            elif line.startswith('VARIANT C'):
                if current_variant and current_message:
                    variants[current_variant] = ' '.join(current_message).strip()
                current_variant = 'variant_c'
                current_message = []
                if ':' in line:
                    message_part = line.split(':', 1)[1].strip()
                    if message_part:
                        current_message.append(message_part)
            
            elif current_variant and line:
                # Skip lines that are just formatting
                if not line.startswith('**') and not line.startswith('---') and not line.startswith('❌') and not line.startswith('✅'):
                    current_message.append(line)
        
        # Add last variant
        if current_variant and current_message:
            variants[current_variant] = ' '.join(current_message).strip()
        
        # Clean up variants (remove extra quotes, trim)
        for key in variants:
            variants[key] = variants[key].strip('"\'').strip()
            # Enforce character limit (200 for LinkedIn connection requests)
            if len(variants[key]) > 200:
                variants[key] = variants[key][:197] + "..."
        
        return variants
    
    def _get_fallback_variants(self, lead: Dict) -> Dict[str, str]:
        """Natural fallback variants if API fails"""
        
        first_name = lead.get('name', '').split()[0] if lead.get('name') else 'there'
        title = lead.get('title', 'your role')
        company = lead.get('company', 'your company')
        
        return {
            'variant_a': f"Hey {first_name}, fellow {title} here - would love to connect and swap notes",
            'variant_b': f"Hi {first_name}, I help {title}s with lead gen. Worth a quick chat?",
            'variant_c': f"{first_name}, respect what you're building at {company}. Let's connect?"
        }
    
    def batch_generate(self, lead_ids: List[int], max_leads: int = 20) -> Dict:
        """
        Generate A/B/C variants for multiple leads
        
        Args:
            lead_ids: List of lead IDs to generate messages for
            max_leads: Maximum number of leads to process
            
        Returns:
            Dict with results summary
        """
        
        results = {
            'successful': 0,
            'failed': 0,
            'messages_created': 0,
            'lead_ids_processed': []
        }
        
        # Limit to max_leads
        lead_ids = lead_ids[:max_leads]
        
        print(f"\n🎨 Generating A/B/C messages for {len(lead_ids)} leads...")
        
        for i, lead_id in enumerate(lead_ids, 1):
            try:
                # Get lead data
                lead = db_manager.get_lead_by_id(lead_id)
                
                if not lead:
                    print(f"❌ [{i}/{len(lead_ids)}] Lead {lead_id} not found")
                    results['failed'] += 1
                    continue
                
                print(f"\n📝 [{i}/{len(lead_ids)}] {lead['name']} ({lead['company']})")
                
                # Check if messages already exist
                existing = db_manager.get_messages_by_lead(lead_id)
                if existing:
                    print(f"   ⚠️ Messages already exist, skipping...")
                    results['failed'] += 1
                    continue
                
                # Generate variants
                variants = self.generate_variants(lead)
                
                # Save to database
                for variant_key, content in variants.items():
                    variant_letter = variant_key.split('_')[1].upper()  # 'variant_a' -> 'A'
                    
                    message_id = db_manager.create_message(
                        lead_id=lead_id,
                        message_type='connection_request',
                        content=content,
                        variant=variant_letter,
                        generated_by='gpt-4',
                        prompt_used=f"ABC variant {variant_letter}",
                        status='draft'
                    )
                    
                    if message_id:
                        results['messages_created'] += 1
                        print(f"   ✅ Variant {variant_letter}: {content[:60]}...")
                
                results['successful'] += 1
                results['lead_ids_processed'].append(lead_id)
                
            except Exception as e:
                print(f"❌ Error processing lead {lead_id}: {str(e)}")
                results['failed'] += 1
        
        print(f"\n✅ Complete: {results['successful']} leads, {results['messages_created']} messages created")
        
        return results


# Quick test function
def test_generator():
    """Test the ABC message generator"""
    
    print("\n" + "="*60)
    print("🧪 ABC MESSAGE GENERATOR TEST")
    print("="*60)
    
    # Get a sample lead
    leads = db_manager.get_all_leads(min_score=70, limit=1)
    
    if not leads:
        print("❌ No leads found to test with")
        return
    
    lead = leads[0]
    
    print(f"\nTest Lead: {lead['name']}")
    print(f"Title: {lead['title']}")
    print(f"Company: {lead['company']}")
    
    generator = ABCMessageGenerator()
    variants = generator.generate_variants(lead)
    
    print("\n📝 Generated Variants:")
    for key, message in variants.items():
        print(f"\n{key.upper().replace('_', ' ')}:")
        print(f"  {message}")
        print(f"  ({len(message)} chars)")


if __name__ == "__main__":
    test_generator()