"""
SC AI Lead Generation System - AI Message Generator
Generate personalized LinkedIn messages using GPT-4
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI package not available. Install with: pip install openai")

from backend.config import Config


class MessageGenerator:
    """Generate personalized LinkedIn messages using AI"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize message generator"""
        self.api_key = openai_api_key or Config.OPENAI_API_KEY
        self.client = None
        
        # Initialize OpenAI if available
        if OPENAI_AVAILABLE and self.api_key and not self.api_key.startswith('sk-your-'):
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ OpenAI client initialized for message generation")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {str(e)}")
                self.client = None
    
    def generate_messages(self, lead_data: Dict, persona_data: Dict, 
                         num_variants: int = 3) -> Dict:
        """
        Generate all message types for a lead
        
        Args:
            lead_data: Dict with name, title, company, etc.
            persona_data: Dict with persona info, pain points, goals, tone
            num_variants: Number of variants to generate (A, B, C)
            
        Returns:
            Dict with all message types and variants
        """
        if not self.client:
            return self._get_fallback_messages(lead_data, persona_data, num_variants)
        
        try:
            messages = {
                'connection_request': [],
                'follow_up_1': [],
                'follow_up_2': []
            }
            
            # Generate each message type
            for message_type in messages.keys():
                for variant_num in range(num_variants):
                    variant_letter = chr(65 + variant_num)  # A, B, C
                    
                    message = self._generate_single_message(
                        lead_data=lead_data,
                        persona_data=persona_data,
                        message_type=message_type,
                        variant=variant_letter
                    )
                    
                    messages[message_type].append({
                        'variant': variant_letter,
                        'content': message['content'],
                        'prompt_used': message['prompt']
                    })
            
            return {
                'success': True,
                'messages': messages,
                'lead_name': lead_data.get('name'),
                'persona': persona_data.get('name')
            }
            
        except Exception as e:
            print(f"❌ Error generating messages: {str(e)}")
            return self._get_fallback_messages(lead_data, persona_data, num_variants)
    
    def _generate_single_message(self, lead_data: Dict, persona_data: Dict,
                                 message_type: str, variant: str) -> Dict:
        """Generate a single message using GPT-4"""
        
        # Build context from lead and persona
        lead_name = lead_data.get('name', 'there')
        first_name = lead_name.split()[0] if lead_name else 'there'
        title = lead_data.get('title', 'professional')
        company = lead_data.get('company', 'your company')
        
        persona_name = persona_data.get('name', 'Professional')
        pain_points = persona_data.get('pain_points', 'growing your business')
        goals = persona_data.get('goals', 'achieving success')
        message_tone = persona_data.get('message_tone', 'professional and consultative')
        key_message = persona_data.get('key_message', 'helping you grow')
        
        # Create prompt based on message type
        prompt = self._build_prompt(
            message_type=message_type,
            variant=variant,
            first_name=first_name,
            title=title,
            company=company,
            persona_name=persona_name,
            pain_points=pain_points,
            goals=goals,
            message_tone=message_tone,
            key_message=key_message
        )
        
        # Call GPT-4
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert LinkedIn copywriter specializing in B2B outreach for the aesthetics industry. Write concise, personalized, high-converting messages."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove quotes if present
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]
            if content.startswith("'") and content.endswith("'"):
                content = content[1:-1]
            
            return {
                'content': content,
                'prompt': prompt
            }
            
        except Exception as e:
            print(f"❌ GPT-4 call failed: {str(e)}")
            return {
                'content': self._get_fallback_single_message(message_type, first_name, title, company),
                'prompt': prompt
            }
    
    def _build_prompt(self, message_type: str, variant: str, first_name: str,
                     title: str, company: str, persona_name: str, pain_points: str,
                     goals: str, message_tone: str, key_message: str) -> str:
        """Build GPT-4 prompt for message generation"""
        
        if message_type == 'connection_request':
            return f"""Write a LinkedIn connection request message for {first_name}, a {title} at {company}.

**Persona**: {persona_name}
**Their Pain Points**: {pain_points}
**Their Goals**: {goals}
**Tone**: {message_tone}
**Value Proposition**: {key_message}

**Requirements**:
- Maximum 300 characters (LinkedIn limit)
- Mention their specific role or company
- Reference one pain point or goal naturally
- Don't use salesy language
- No buzzwords or jargon
- Be genuine and conversational
- Variant {variant}: {'Make it direct and results-focused' if variant == 'A' else 'Make it collaborative and relationship-focused' if variant == 'B' else 'Make it curiosity-driven with a question'}

Write ONLY the message, no subject line or explanation."""

        elif message_type == 'follow_up_1':
            return f"""Write a LinkedIn follow-up message for {first_name}, a {title} at {company}. They accepted your connection request 2-3 days ago.

**Persona**: {persona_name}
**Their Pain Points**: {pain_points}
**Their Goals**: {goals}
**Tone**: {message_tone}
**Value Proposition**: {key_message}

**Requirements**:
- 3-4 sentences maximum
- Thank them for connecting
- Provide value or insight related to their role
- Reference their specific industry or challenge
- Include a soft call-to-action (not pushy)
- Variant {variant}: {'Focus on data/results' if variant == 'A' else 'Focus on case study/social proof' if variant == 'B' else 'Focus on offering help/resource'}

Write ONLY the message, no subject line."""

        else:  # follow_up_2
            return f"""Write a second LinkedIn follow-up message for {first_name}, a {title} at {company}. They haven't responded to your first follow-up from 5 days ago.

**Persona**: {persona_name}
**Their Pain Points**: {pain_points}
**Their Goals**: {goals}
**Tone**: {message_tone}
**Value Proposition**: {key_message}

**Requirements**:
- 2-3 sentences maximum
- Acknowledge they're busy
- Offer a specific next step (brief call, resource, demo)
- Make it easy to say yes with specific time options
- Use urgency without being pushy
- Variant {variant}: {'Direct meeting request with time options' if variant == 'A' else 'Share valuable resource with soft ask' if variant == 'B' else 'Ask permission to share something relevant'}

Write ONLY the message, no subject line."""
    
    def _get_fallback_messages(self, lead_data: Dict, persona_data: Dict, 
                               num_variants: int) -> Dict:
        """Generate fallback template messages when AI is unavailable"""
        
        first_name = lead_data.get('name', 'there').split()[0]
        title = lead_data.get('title', 'professional')
        company = lead_data.get('company', 'your company')
        
        messages = {
            'connection_request': [
                {
                    'variant': 'A',
                    'content': f"Hi {first_name}, I work with {title}s to improve their digital presence and patient acquisition. Would love to connect!",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'B',
                    'content': f"Hi {first_name}, impressed by your work at {company}. I'd love to share some insights on growing aesthetic practices.",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'C',
                    'content': f"Hi {first_name}, connecting with {title}s in the aesthetics space. Would you be open to exchanging ideas?",
                    'prompt_used': 'fallback_template'
                }
            ][:num_variants],
            
            'follow_up_1': [
                {
                    'variant': 'A',
                    'content': f"Thanks for connecting, {first_name}! I work with {title}s to increase patient bookings by 30-50%. Our clients see results in 60-90 days. Would you be interested in learning how?",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'B',
                    'content': f"Hi {first_name}, great to connect! I recently helped a {title} at a similar practice increase their cosmetic procedure bookings significantly. Would you like to see the case study?",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'C',
                    'content': f"Thanks for connecting, {first_name}! I have a resource on patient acquisition strategies for {title}s that you might find valuable. Can I share it with you?",
                    'prompt_used': 'fallback_template'
                }
            ][:num_variants],
            
            'follow_up_2': [
                {
                    'variant': 'A',
                    'content': f"Hi {first_name}, I know you're busy! Would you have 15 minutes next Tuesday or Wednesday to discuss how we can help {company} grow? Let me know what works.",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'B',
                    'content': f"{first_name}, I came across this guide on digital marketing for aesthetic practices and thought of you. Can I send it over? No strings attached.",
                    'prompt_used': 'fallback_template'
                },
                {
                    'variant': 'C',
                    'content': f"Hi {first_name}, would it be helpful if I shared how other {title}s are handling patient acquisition challenges? Happy to hop on a quick call if interested.",
                    'prompt_used': 'fallback_template'
                }
            ][:num_variants]
        }
        
        return {
            'success': True,
            'messages': messages,
            'lead_name': lead_data.get('name'),
            'persona': persona_data.get('name'),
            'note': 'Using fallback templates (OpenAI not configured)'
        }
    
    def _get_fallback_single_message(self, message_type: str, first_name: str,
                                    title: str, company: str) -> str:
        """Get a single fallback message"""
        
        templates = {
            'connection_request': f"Hi {first_name}, I work with {title}s to grow their practice. Would love to connect!",
            'follow_up_1': f"Thanks for connecting, {first_name}! I help {title}s increase patient bookings. Would you be interested in learning more?",
            'follow_up_2': f"Hi {first_name}, would you have 15 minutes this week to discuss how we can help {company}?"
        }
        
        return templates.get(message_type, f"Hi {first_name}, looking forward to connecting!")
    
    def generate_single_type(self, lead_data: Dict, persona_data: Dict,
                            message_type: str, variant: str = 'A') -> Dict:
        """Generate a single message of specific type and variant"""
        
        if not self.client:
            messages = self._get_fallback_messages(lead_data, persona_data, 3)
            variants = messages['messages'][message_type]
            selected = next((v for v in variants if v['variant'] == variant), variants[0])
            return {
                'success': True,
                'content': selected['content'],
                'prompt_used': selected['prompt_used'],
                'variant': variant,
                'message_type': message_type
            }
        
        try:
            message = self._generate_single_message(
                lead_data=lead_data,
                persona_data=persona_data,
                message_type=message_type,
                variant=variant
            )
            
            return {
                'success': True,
                'content': message['content'],
                'prompt_used': message['prompt'],
                'variant': variant,
                'message_type': message_type
            }
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'content': self._get_fallback_single_message(message_type, 
                                                            lead_data.get('name', 'there').split()[0],
                                                            lead_data.get('title', 'professional'),
                                                            lead_data.get('company', 'your company'))
            }


# Singleton instance
_message_generator = None

def get_message_generator(api_key: str = None) -> MessageGenerator:
    """Get or create message generator instance"""
    global _message_generator
    if _message_generator is None:
        _message_generator = MessageGenerator(openai_api_key=api_key)
    return _message_generator


# Convenience functions
def generate_all_messages(lead_data: Dict, persona_data: Dict, 
                         num_variants: int = 3, api_key: str = None) -> Dict:
    """Generate all message types - convenience wrapper"""
    generator = get_message_generator(api_key=api_key)
    return generator.generate_messages(lead_data, persona_data, num_variants)


def generate_message(lead_data: Dict, persona_data: Dict, 
                    message_type: str, variant: str = 'A', api_key: str = None) -> Dict:
    """Generate single message - convenience wrapper"""
    generator = get_message_generator(api_key=api_key)
    return generator.generate_single_type(lead_data, persona_data, message_type, variant)


# CLI for testing
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🧪 Testing Message Generator")
    print("="*70)
    
    # Test data
    test_lead = {
        'name': 'Dr. Sarah Johnson',
        'title': 'Medical Director & Owner',
        'company': 'Beverly Hills Aesthetics',
        'location': 'Los Angeles, CA'
    }
    
    test_persona = {
        'name': 'Plastic Surgeon',
        'description': 'The Prestige Provider',
        'pain_points': 'Competing with med-spas, inconsistent patient flow, website doesn\'t reflect brand quality',
        'goals': 'Attract high-value cosmetic cases, build strong regional reputation, fill schedule with elective procedures',
        'message_tone': 'Consultative, prestige-focused',
        'key_message': 'Grow your reputation and patient bookings with proven digital systems built for plastic surgeons'
    }
    
    # Generate all messages
    print(f"\n👤 Lead: {test_lead['name']}")
    print(f"💼 Title: {test_lead['title']}")
    print(f"🎯 Persona: {test_persona['name']}\n")
    
    result = generate_all_messages(test_lead, test_persona, num_variants=3)
    
    if result['success']:
        for msg_type, variants in result['messages'].items():
            print(f"\n📧 {msg_type.upper().replace('_', ' ')}")
            print("-" * 70)
            for variant_data in variants:
                print(f"\n  Variant {variant_data['variant']}:")
                print(f"  {variant_data['content']}")
        
        print("\n" + "="*70)
        print("✅ Message generation test complete!")
        print("="*70)
    else:
        print("❌ Message generation failed!")