"""
A/B/C Message Variant Generator
Generates 3 different message variants for testing
ENHANCED: Full A/B test integration with automatic variant assignment
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager


class ABCMessageGenerator:
    """Generate A/B/C message variants for leads with AB testing"""
    
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
        
        prompt = self._build_prompt(lead_data, persona_data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert LinkedIn outreach specialist who creates personalized connection requests that get responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            variants = self._parse_variants(content)
            
            return variants
            
        except Exception as e:
            print(f"Error generating variants: {str(e)}")
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
            parts = content.split('VARIANT_')
            
            for part in parts:
                if part.startswith('A:'):
                    variants['variant_a'] = part.replace('A:', '').strip()
                elif part.startswith('B:'):
                    variants['variant_b'] = part.replace('B:', '').strip()
                elif part.startswith('C:'):
                    variants['variant_c'] = part.replace('C:', '').strip()
            
            if not all(variants.values()):
                raise ValueError("Missing variants in response")
            
            return variants
            
        except Exception as e:
            print(f"Error parsing variants: {str(e)}")
            print(f"Raw content: {content}")
            raise
    
    def _generate_fallback_variants(self, lead_data: Dict, persona_data: Dict) -> Dict[str, str]:
        """Generate simple template-based variants as fallback"""
        
        name = lead_data.get('name', 'there').split()[0]
        title = lead_data.get('title', 'professional')
        company = lead_data.get('company', 'your company')
        
        variants = {
            'variant_a': f"Hi {name}, I help {title}s at companies like {company} achieve their goals. Would love to connect and share insights that could help you.",
            
            'variant_b': f"Hi {name}, quick question - what's your biggest challenge as a {title} at {company} right now? I might have some helpful insights to share.",
            
            'variant_c': f"Hi {name}, I specialize in helping {title}s like you at {company}. I've helped similar professionals achieve great results. Let's connect!"
        }
        
        return variants
    
    def generate_for_lead(self, lead_id: int, test_id: int = None, save_to_db: bool = True) -> Dict:
        """
        Generate A/B/C variants for a specific lead and optionally save to database
        
        Args:
            lead_id: Lead ID from database
            test_id: Optional AB test ID to link messages to
            save_to_db: Whether to save messages to database
            
        Returns:
            Dict with variants and metadata
        """
        
        lead = db_manager.get_lead_by_id(lead_id)
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        persona_id = lead.get('persona_id')
        persona = db_manager.get_persona_by_id(persona_id) if persona_id else {}
        
        print(f"Generating A/B/C variants for: {lead.get('name')}")
        variants = self.generate_variants(lead, persona)
        
        if save_to_db:
            saved_ids = []
            
            for variant_letter, content in [
                ('A', variants['variant_a']),
                ('B', variants['variant_b']),
                ('C', variants['variant_c'])
            ]:
                # Create message with AB test link
                message_id = db_manager.create_message(
                    lead_id=lead_id,
                    message_type='connection_request',
                    content=content,
                    variant=variant_letter,
                    generated_by='gpt-4',
                    status='draft'
                )
                
                # Link to AB test if provided
                if test_id and message_id:
                    with db_manager.session_scope() as session:
                        from backend.database.models import Message
                        message = session.query(Message).filter(Message.id == message_id).first()
                        if message:
                            message.ab_test_id = test_id
                
                saved_ids.append(message_id)
            
            print(f"✅ Saved 3 variants to database (IDs: {saved_ids})")
            
            if test_id:
                print(f"🔗 Linked to AB Test ID: {test_id}")
            
            return {
                'success': True,
                'lead_id': lead_id,
                'lead_name': lead.get('name'),
                'variants': variants,
                'message_ids': saved_ids,
                'test_id': test_id
            }
        
        return {
            'success': True,
            'lead_id': lead_id,
            'lead_name': lead.get('name'),
            'variants': variants
        }
    
    def batch_generate(self, lead_ids: List[int], max_leads: int = 20, 
                      test_name: str = None, campaign_id: int = None,
                      create_ab_test: bool = True) -> Dict:
        """
        Generate A/B/C message variants for multiple leads
        Automatically creates an A/B test and assigns variants
        
        Args:
            lead_ids: List of lead IDs
            max_leads: Maximum number of leads to process
            test_name: Name for the AB test
            campaign_id: Optional campaign ID
            create_ab_test: Whether to create an AB test
            
        Returns:
            Dict with results and AB test info
        """
        from datetime import datetime
        
        # Limit to max_leads
        lead_ids = lead_ids[:max_leads]
        
        test_id = None
        if create_ab_test:
            if not test_name:
                test_name = f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create A/B test
            test_id = db_manager.create_ab_test(
                test_name=test_name,
                campaign_id=campaign_id,
                min_sends=min(20, len(lead_ids))
            )
            
            print(f"🧪 Created A/B Test: {test_name} (ID: {test_id})")
        
        successful = 0
        failed = 0
        messages_created = 0
        
        for lead_id in lead_ids:
            try:
                lead = db_manager.get_lead_by_id(lead_id)
                if not lead:
                    print(f"⚠️ Lead {lead_id} not found")
                    failed += 1
                    continue
                
                persona = None
                if lead.get('persona_id'):
                    persona = db_manager.get_persona_by_id(lead['persona_id'])
                
                # Generate 3 variants
                variants = self.generate_variants(lead, persona)
                
                # Save all 3 variants with A/B test assignment
                for variant_letter in ['A', 'B', 'C']:
                    variant_key = f'variant_{variant_letter.lower()}'
                    
                    message_id = db_manager.create_message(
                        lead_id=lead_id,
                        message_type='connection_request',
                        content=variants[variant_key],
                        campaign_id=campaign_id,
                        variant=variant_letter,
                        status='draft',
                        generated_by='gpt-4'
                    )
                    
                    # Link to AB test
                    if test_id and message_id:
                        with db_manager.session_scope() as session:
                            from backend.database.models import Message
                            message = session.query(Message).filter(Message.id == message_id).first()
                            if message:
                                message.ab_test_id = test_id
                    
                    if message_id:
                        messages_created += 1
                
                successful += 1
                print(f"  ✅ Generated 3 variants for {lead['name']}")
                
            except Exception as e:
                print(f"  ❌ Failed for lead {lead_id}: {str(e)}")
                failed += 1
        
        print(f"\n✅ Generated {messages_created} total messages")
        print(f"   Success: {successful} leads | Failed: {failed} leads")
        
        result = {
            'test_id': test_id,
            'test_name': test_name,
            'total_leads': len(lead_ids),
            'successful': successful,
            'failed': failed,
            'messages_created': messages_created
        }
        
        if test_id:
            result['test_url'] = f'http://localhost:5000/api/ab-tests/{test_id}'
        
        return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate A/B/C Message Variants')
    parser.add_argument('--lead-id', type=int, help='Generate for specific lead ID')
    parser.add_argument('--top', type=int, default=20, help='Generate for top N leads')
    parser.add_argument('--test', action='store_true', help='Test with first lead')
    parser.add_argument('--test-name', type=str, help='AB test name')
    parser.add_argument('--no-ab-test', action='store_true', help='Skip AB test creation')
    
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    generator = ABCMessageGenerator(api_key=api_key)
    
    if args.test:
        leads = db_manager.get_all_leads(limit=1)
        if leads:
            # Create test AB test
            test_id = db_manager.create_ab_test("CLI_Test") if not args.no_ab_test else None
            
            result = generator.generate_for_lead(
                leads[0]['id'], 
                test_id=test_id,
                save_to_db=True
            )
            print(f"\n✅ Generated variants for: {result['lead_name']}")
            print(f"\nVARIANT A:\n{result['variants']['variant_a']}\n")
            print(f"VARIANT B:\n{result['variants']['variant_b']}\n")
            print(f"VARIANT C:\n{result['variants']['variant_c']}\n")
            
            if test_id:
                print(f"🧪 AB Test ID: {test_id}")
        else:
            print("❌ No leads found in database")
    
    elif args.lead_id:
        test_id = None
        if not args.no_ab_test:
            test_id = db_manager.create_ab_test(
                args.test_name or f"Single_Lead_{args.lead_id}"
            )
        
        result = generator.generate_for_lead(
            args.lead_id, 
            test_id=test_id,
            save_to_db=True
        )
        print(f"\n✅ Generated variants for: {result['lead_name']}")
    
    else:
        leads = db_manager.get_all_leads(min_score=70, limit=args.top)
        lead_ids = [lead['id'] for lead in leads]
        
        if not lead_ids:
            print("❌ No qualified leads found (score >= 70)")
            sys.exit(1)
        
        print(f"🚀 Generating A/B/C variants for top {len(lead_ids)} leads...")
        results = generator.batch_generate(
            lead_ids,
            test_name=args.test_name,
            create_ab_test=not args.no_ab_test
        )
        
        print(f"\n📊 RESULTS:")
        print(f"  ✅ Successful: {results['successful']}")
        print(f"  ❌ Failed: {results['failed']}")
        print(f"  💬 Messages created: {results['messages_created']}")
        
        if results.get('test_id'):
            print(f"  🧪 AB Test ID: {results['test_id']}")
            print(f"  🔗 View results: {results['test_url']}")