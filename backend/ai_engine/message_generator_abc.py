"""
A/B/C Message Variant Generator
Generates 3 different message variants for testing
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager


class ABCMessageGenerator:
    """Generate A/B/C message variants for leads"""
    
    def __init__(self, api_key: str = None):
        """Initialize generator with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_variants(self, lead_data: Dict, persona_data: Dict) -> Dict[str, str]:
        """
        Generate 3 message variants (A, B, C) for a lead
        
        Args:
            lead_data: Lead information (name, title, company, etc.)
            persona_data: Target persona details
            
        Returns:
            Dict with variants: {'variant_a': str, 'variant_b': str, 'variant_c': str}
        """
        
        # Build prompt for GPT-4
        prompt = self._build_prompt(lead_data, persona_data)
        
        try:
            # Call GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert LinkedIn outreach specialist who creates personalized connection requests that get responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            variants = self._parse_variants(content)
            
            return variants
            
        except Exception as e:
            print(f"Error generating variants: {str(e)}")
            # Fallback to template-based messages
            return self._generate_fallback_variants(lead_data, persona_data)
    
    def _build_prompt(self, lead_data: Dict, persona_data: Dict) -> str:
        """Build GPT-4 prompt for generating variants"""
        
        lead_name = lead_data.get('name', 'there')
        lead_title = lead_data.get('title', 'Professional')
        lead_company = lead_data.get('company', 'your company')
        
        persona_name = persona_data.get('name', 'Professional')
        persona_goals = persona_data.get('goals', '')
        persona_pain_points = persona_data.get('pain_points', '')
        
        prompt = f"""Generate 3 LinkedIn connection request message variants for this lead:

LEAD INFO:
- Name: {lead_name}
- Title: {lead_title}
- Company: {lead_company}

TARGET PERSONA: {persona_name}
- Goals: {persona_goals[:200]}
- Pain Points: {persona_pain_points[:200]}

REQUIREMENTS:
1. Each message must be under 300 characters (LinkedIn limit)
2. Personalized to {lead_name} and their role at {lead_company}
3. Address their likely pain points or goals
4. Include a clear call-to-action

Generate 3 DIFFERENT variants:

VARIANT A: Direct and value-focused
- Lead with a specific benefit or insight
- Professional but confident tone
- Clear value proposition

VARIANT B: Curiosity-driven and question-based
- Start with an intriguing question
- More casual and conversational tone
- Make them curious to learn more

VARIANT C: Social proof and authority
- Mention relevant credibility or results
- More formal and authoritative tone
- Establish expertise

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

VARIANT_A:
[Your message here]

VARIANT_B:
[Your message here]

VARIANT_C:
[Your message here]"""

        return prompt
    
    def _parse_variants(self, content: str) -> Dict[str, str]:
        """Parse GPT-4 response into A/B/C variants"""
        
        variants = {
            'variant_a': '',
            'variant_b': '',
            'variant_c': ''
        }
        
        try:
            # Split by variant markers
            parts = content.split('VARIANT_')
            
            for part in parts:
                if part.startswith('A:'):
                    variants['variant_a'] = part.replace('A:', '').strip()
                elif part.startswith('B:'):
                    variants['variant_b'] = part.replace('B:', '').strip()
                elif part.startswith('C:'):
                    variants['variant_c'] = part.replace('C:', '').strip()
            
            # Validate all variants exist
            if not all(variants.values()):
                raise ValueError("Missing variants in response")
            
            return variants
            
        except Exception as e:
            print(f"Error parsing variants: {str(e)}")
            print(f"Raw content: {content}")
            raise
    
    def _generate_fallback_variants(self, lead_data: Dict, persona_data: Dict) -> Dict[str, str]:
        """Generate simple template-based variants as fallback"""
        
        name = lead_data.get('name', 'there').split()[0]  # First name
        title = lead_data.get('title', 'professional')
        company = lead_data.get('company', 'your company')
        
        variants = {
            'variant_a': f"Hi {name}, I help {title}s at companies like {company} achieve their goals. Would love to connect and share insights that could help you.",
            
            'variant_b': f"Hi {name}, quick question - what's your biggest challenge as a {title} at {company} right now? I might have some helpful insights to share.",
            
            'variant_c': f"Hi {name}, I specialize in helping {title}s like you at {company}. I've helped similar professionals achieve great results. Let's connect!"
        }
        
        return variants
    
    def generate_for_lead(self, lead_id: int, save_to_db: bool = True) -> Dict:
        """
        Generate A/B/C variants for a specific lead and optionally save to database
        
        Args:
            lead_id: Lead ID from database
            save_to_db: Whether to save messages to database
            
        Returns:
            Dict with variants and metadata
        """
        
        # Get lead from database
        lead = db_manager.get_lead_by_id(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        # Get persona for this lead
        persona_id = lead.get('persona_id')
        persona = db_manager.get_persona_by_id(persona_id) if persona_id else {}
        
        # Generate variants
        print(f"Generating A/B/C variants for: {lead.get('name')}")
        variants = self.generate_variants(lead, persona)
        
        # Save to database if requested
        if save_to_db:
            saved_ids = []
            for variant_letter, content in [
                ('A', variants['variant_a']),
                ('B', variants['variant_b']),
                ('C', variants['variant_c'])
            ]:
                message_id = db_manager.create_message(
                    lead_id=lead_id,
                    message_type='connection_request',
                    content=content,
                    variant=variant_letter,
                    generated_by='gpt-4',
                    status='draft'
                )
                saved_ids.append(message_id)
            
            print(f"✅ Saved 3 variants to database (IDs: {saved_ids})")
            
            return {
                'success': True,
                'lead_id': lead_id,
                'lead_name': lead.get('name'),
                'variants': variants,
                'message_ids': saved_ids
            }
        
        return {
            'success': True,
            'lead_id': lead_id,
            'lead_name': lead.get('name'),
            'variants': variants
        }
    
    def batch_generate(self, lead_ids: List[int], max_leads: int = 20) -> Dict:
        """
        Generate A/B/C variants for multiple leads
        
        Args:
            lead_ids: List of lead IDs
            max_leads: Maximum number of leads to process
            
        Returns:
            Summary of generation results
        """
        
        lead_ids = lead_ids[:max_leads]  # Limit to max
        
        results = {
            'total': len(lead_ids),
            'successful': 0,
            'failed': 0,
            'messages_created': 0,
            'details': []
        }
        
        for lead_id in lead_ids:
            try:
                result = self.generate_for_lead(lead_id, save_to_db=True)
                results['successful'] += 1
                results['messages_created'] += 3  # A, B, C
                results['details'].append(result)
                
            except Exception as e:
                print(f"❌ Failed for lead {lead_id}: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'success': False,
                    'lead_id': lead_id,
                    'error': str(e)
                })
        
        return results


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate A/B/C Message Variants')
    parser.add_argument('--lead-id', type=int, help='Generate for s