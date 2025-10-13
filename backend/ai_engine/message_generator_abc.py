"""
SC AI Lead Generation System - A/B/C Message Generator
Generates 3 message variants (A, B, C) for each lead for testing
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
        Generate 3 message variants (A, B, C) for a single lead
        
        Args:
            lead: Dict with lead information (name, title, company, persona)
            
        Returns:
            Dict with keys: variant_a, variant_b, variant_c
        """
        
        prompt = f"""You are an expert LinkedIn outreach specialist. Generate 3 DIFFERENT message variants for this lead:

**Lead Information:**
- Name: {lead.get('name', 'Professional')}
- Title: {lead.get('title', 'Professional')}
- Company: {lead.get('company', 'their company')}
- Persona: {lead.get('persona_name', 'Business Professional')}
- AI Score: {lead.get('ai_score', 'N/A')}/100

**Generate 3 variants with different approaches:**

**Variant A - Direct Value:**
- Lead with specific value proposition
- Mention their role/company directly
- Clear call-to-action
- Professional but warm
- 250-300 characters max

**Variant B - Curiosity/Question:**
- Start with engaging question
- Reference their industry/challenges
- Create curiosity gap
- More conversational tone
- 250-300 characters max

**Variant C - Social Proof:**
- Reference similar clients/results
- Use credibility indicators
- Show expertise
- Confidence-building
- 250-300 characters max

**CRITICAL REQUIREMENTS:**
1. Each variant MUST be genuinely different (not just word swaps)
2. All under 300 characters (LinkedIn connection request limit)
3. Personalized to their role and company
4. No generic templates
5. Professional but human
6. No emojis unless absolutely natural

**Format your response EXACTLY like this:**

VARIANT A:
[Your variant A message here]

VARIANT B:
[Your variant B message here]

VARIANT C:
[Your variant C message here]
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert B2B LinkedIn outreach specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher for more variety
                max_tokens=800
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
                if not line.startswith('**') and not line.startswith('---'):
                    current_message.append(line)
        
        # Add last variant
        if current_variant and current_message:
            variants[current_variant] = ' '.join(current_message).strip()
        
        # Clean up variants (remove extra quotes, trim)
        for key in variants:
            variants[key] = variants[key].strip('"\'').strip()
            # Enforce character limit
            if len(variants[key]) > 300:
                variants[key] = variants[key][:297] + "..."
        
        return variants
    
    def _get_fallback_variants(self, lead: Dict) -> Dict[str, str]:
        """Fallback variants if API fails"""
        
        name = lead.get('name', 'there')
        title = lead.get('title', 'your role')
        company = lead.get('company', 'your company')
        
        return {
            'variant_a': f"Hi {name}, I help {title}s at companies like {company} streamline their lead generation. Would love to connect and share some insights that could be valuable.",
            'variant_b': f"Hi {name}, curious - how are you currently handling lead generation at {company}? I work with {title}s to automate their outreach and would love to exchange ideas.",
            'variant_c': f"Hi {name}, we've helped several {title}s increase their qualified leads by 300%+. Given your work at {company}, thought you might find our approach interesting. Connect?"
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