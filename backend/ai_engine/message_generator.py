"""
SC AI Lead Generation System - Message Generator
GPT-4 powered personalized message generation for LinkedIn outreach
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import openai
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from backend.config import Config
    from backend.database.db_manager import db_manager
    USE_DATABASE = True
except ImportError:
    print("⚠️ Warning: Database modules not available")
    USE_DATABASE = False
    class Config:
        pass


class MessageGenerator:
    """Generate personalized LinkedIn messages using GPT-4"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize message generator
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        openai.api_key = self.api_key
        self.model = "gpt-4"
        self.temperature = 0.7
    
    def generate_connection_request(self, 
                                   lead_name: str,
                                   lead_title: str,
                                   lead_company: str,
                                   persona_name: str = None,
                                   persona_description: str = None,
                                   custom_context: str = None) -> Dict[str, str]:
        """
        Generate a personalized LinkedIn connection request message
        
        Args:
            lead_name: Name of the lead
            lead_title: Job title of the lead
            lead_company: Company name
            persona_name: Target persona name (e.g., "Marketing Agencies")
            persona_description: Additional persona context
            custom_context: Any additional context to include
            
        Returns:
            Dict with 3 message variants (A, B, C)
        """
        
        # Build the prompt
        prompt = f"""You are an expert B2B sales copywriter specializing in LinkedIn outreach.

Generate 3 variations of a LinkedIn connection request message for the following lead:

**Lead Information:**
- Name: {lead_name}
- Title: {lead_title}
- Company: {lead_company}
{f"- Target Persona: {persona_name}" if persona_name else ""}
{f"- Persona Context: {persona_description}" if persona_description else ""}
{f"- Additional Context: {custom_context}" if custom_context else ""}

**Requirements:**
1. Maximum 300 characters (LinkedIn connection request limit)
2. Personalized to their role and company
3. Clear value proposition
4. Professional but warm tone
5. No pushy sales language
6. End with a soft call-to-action

**Generate 3 variants:**
- Variant A: Direct and value-focused
- Variant B: Curiosity-driven and conversational
- Variant C: Authority-based with social proof

Format your response EXACTLY like this:

VARIANT_A:
[message text here]

VARIANT_B:
[message text here]

VARIANT_C:
[message text here]
"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert LinkedIn copywriter focused on high-conversion connection requests."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=600
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            variants = self._parse_variants(content)
            
            # Validate character limits
            for key, message in variants.items():
                if len(message) > 300:
                    variants[key] = message[:297] + "..."
            
            return variants
        
        except Exception as e:
            print(f"❌ Error generating connection request: {str(e)}")
            return self._get_fallback_connection_messages(lead_name, lead_title, lead_company)
    
    def generate_follow_up_message(self,
                                   lead_name: str,
                                   lead_title: str,
                                   lead_company: str,
                                   persona_name: str = None,
                                   message_number: int = 1,
                                   previous_message: str = None) -> Dict[str, str]:
        """
        Generate follow-up message after connection is accepted
        
        Args:
            lead_name: Name of the lead
            lead_title: Job title
            lead_company: Company name
            persona_name: Target persona
            message_number: 1 for first follow-up, 2 for second
            previous_message: Previous message sent (for context)
            
        Returns:
            Dict with 3 message variants
        """
        
        if message_number == 1:
            message_type = "First Follow-Up (2-3 days after connection)"
            goal = "Provide value and start conversation"
        else:
            message_type = "Second Follow-Up (5-7 days after first)"
            goal = "Call-to-action for meeting/demo"
        
        prompt = f"""You are an expert B2B sales copywriter specializing in LinkedIn outreach.

Generate 3 variations of a LinkedIn follow-up message for the following lead:

**Lead Information:**
- Name: {lead_name}
- Title: {lead_title}
- Company: {lead_company}
{f"- Target Persona: {persona_name}" if persona_name else ""}

**Message Type:** {message_type}
**Goal:** {goal}

{f"**Previous Message:** {previous_message}" if previous_message else ""}

**Requirements:**
1. Maximum 500 characters
2. Reference their role/company specifically
3. Provide clear value proposition
4. {"Ask insightful question to start dialogue" if message_number == 1 else "Clear call-to-action (meeting request)"}
5. Professional but personable tone
6. No generic templates

**Generate 3 variants:**
- Variant A: Value-focused with specific benefit
- Variant B: Problem-solution approach
- Variant C: Case study or social proof angle

Format your response EXACTLY like this:

VARIANT_A:
[message text here]

VARIANT_B:
[message text here]

VARIANT_C:
[message text here]
"""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert LinkedIn copywriter focused on high-conversion follow-up messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            variants = self._parse_variants(content)
            
            # Validate character limits
            for key, message in variants.items():
                if len(message) > 500:
                    variants[key] = message[:497] + "..."
            
            return variants
        
        except Exception as e:
            print(f"❌ Error generating follow-up message: {str(e)}")
            return self._get_fallback_followup_messages(lead_name, lead_title, message_number)
    
    def generate_all_messages(self,
                             lead_id: int,
                             save_to_db: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Generate complete message sequence for a lead
        
        Args:
            lead_id: Database ID of the lead
            save_to_db: Whether to save messages to database
            
        Returns:
            Dict with all message types and variants
        """
        
        if not USE_DATABASE:
            raise ValueError("Database access required for this function")
        
        # Get lead from database
        lead = db_manager.get_lead_by_id(lead_id)
        
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        print(f"\n🎨 Generating messages for: {lead['name']}")
        print(f"   Title: {lead['title']}")
        print(f"   Company: {lead['company']}")
        
        # Get persona information
        persona_name = lead.get('persona_name')
        persona_description = None
        
        if lead.get('persona_id'):
            personas = db_manager.get_all_personas()
            persona = next((p for p in personas if p['id'] == lead['persona_id']), None)
            if persona:
                persona_description = persona.get('description')
        
        messages = {}
        
        # 1. Connection Request
        print("\n  📝 Generating connection request...")
        messages['connection_request'] = self.generate_connection_request(
            lead_name=lead['name'],
            lead_title=lead['title'],
            lead_company=lead['company'],
            persona_name=persona_name,
            persona_description=persona_description
        )
        print("     ✅ Done")
        
        # 2. First Follow-Up
        print("  📝 Generating first follow-up...")
        messages['follow_up_1'] = self.generate_follow_up_message(
            lead_name=lead['name'],
            lead_title=lead['title'],
            lead_company=lead['company'],
            persona_name=persona_name,
            message_number=1
        )
        print("     ✅ Done")
        
        # 3. Second Follow-Up
        print("  📝 Generating second follow-up...")
        messages['follow_up_2'] = self.generate_follow_up_message(
            lead_name=lead['name'],
            lead_title=lead['title'],
            lead_company=lead['company'],
            persona_name=persona_name,
            message_number=2,
            previous_message=messages['follow_up_1']['variant_a']
        )
        print("     ✅ Done")
        
        # Save to database
        if save_to_db:
            print("\n  💾 Saving messages to database...")
            self._save_messages_to_db(lead_id, messages)
            print("     ✅ Saved")
        
        print(f"\n✅ Generated {len(messages) * 3} message variants for {lead['name']}")
        
        return messages
    
    def _parse_variants(self, content: str) -> Dict[str, str]:
        """Parse GPT-4 response into variant dictionary"""
        variants = {}
        
        for variant_key in ['VARIANT_A:', 'VARIANT_B:', 'VARIANT_C:']:
            if variant_key in content:
                # Extract message between this variant and the next
                start = content.find(variant_key) + len(variant_key)
                
                # Find the next variant or end of string
                next_variants = [v for v in ['VARIANT_A:', 'VARIANT_B:', 'VARIANT_C:'] if v != variant_key]
                end_positions = [content.find(v, start) for v in next_variants if content.find(v, start) != -1]
                
                if end_positions:
                    end = min(end_positions)
                else:
                    end = len(content)
                
                message = content[start:end].strip()
                
                # Clean up the message
                message = message.replace('\n\n', ' ').replace('\n', ' ')
                message = ' '.join(message.split())  # Remove extra whitespace
                
                # Map to lowercase key
                key = variant_key.lower().replace(':', '').replace('_', '_')
                variants[key] = message
        
        return variants
    
    def _save_messages_to_db(self, lead_id: int, messages: Dict[str, Dict[str, str]]):
        """Save generated messages to database"""
        
        for message_type, variants in messages.items():
            for variant_key, content in variants.items():
                # Extract variant letter (a, b, or c)
                variant = variant_key.split('_')[-1].upper()
                
                db_manager.create_message(
                    lead_id=lead_id,
                    message_type=message_type,
                    content=content,
                    variant=variant,
                    generated_by='gpt-4',
                    prompt_used=f"Generated {message_type} variant {variant}"
                )
    
    def _get_fallback_connection_messages(self, lead_name: str, lead_title: str, lead_company: str) -> Dict[str, str]:
        """Fallback messages if API fails"""
        return {
            'variant_a': f"Hi {lead_name}, I came across your profile and was impressed by your work at {lead_company}. I'd love to connect and exchange ideas about {lead_title} best practices.",
            'variant_b': f"Hi {lead_name}, fellow professional here. Your experience at {lead_company} caught my attention. Would be great to connect!",
            'variant_c': f"Hi {lead_name}, I noticed we both work in similar spaces. Your role as {lead_title} is interesting - let's connect!"
        }
    
    def _get_fallback_followup_messages(self, lead_name: str, lead_title: str, message_number: int) -> Dict[str, str]:
        """Fallback follow-up messages if API fails"""
        if message_number == 1:
            return {
                'variant_a': f"Thanks for connecting, {lead_name}! I'm curious - what are your biggest priorities as a {lead_title} right now?",
                'variant_b': f"Great to connect, {lead_name}! I work with many {lead_title}s and would love to hear about your current challenges.",
                'variant_c': f"Hi {lead_name}, thanks for accepting! I'd love to learn more about your work and see if there's any way I can be helpful."
            }
        else:
            return {
                'variant_a': f"Hi {lead_name}, following up on my last message. Would you be open to a quick 15-minute call to explore potential synergies?",
                'variant_b': f"{lead_name}, I have some insights that might be valuable for your work. Are you available for a brief chat this week?",
                'variant_c': f"Hi {lead_name}, I'd love to show you something that could help with [specific challenge]. Free for a quick call?"
            }


# Standalone functions for easy import
def generate_connection_message(lead_name: str, lead_title: str, lead_company: str, 
                                persona_name: str = None, api_key: str = None) -> Dict[str, str]:
    """
    Quick function to generate connection request
    
    Returns:
        Dict with variant_a, variant_b, variant_c keys
    """
    generator = MessageGenerator(api_key=api_key)
    return generator.generate_connection_request(
        lead_name=lead_name,
        lead_title=lead_title,
        lead_company=lead_company,
        persona_name=persona_name
    )


def generate_followup_message(lead_name: str, lead_title: str, lead_company: str,
                              message_number: int = 1, api_key: str = None) -> Dict[str, str]:
    """
    Quick function to generate follow-up message
    
    Returns:
        Dict with variant_a, variant_b, variant_c keys
    """
    generator = MessageGenerator(api_key=api_key)
    return generator.generate_follow_up_message(
        lead_name=lead_name,
        lead_title=lead_title,
        lead_company=lead_company,
        message_number=message_number
    )


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Message Generator')
    parser.add_argument('--lead-id', type=int, help='Lead ID from database')
    parser.add_argument('--test', action='store_true', help='Run test with sample data')
    
    args = parser.parse_args()
    
    generator = MessageGenerator()
    
    if args.test:
        print("\n🧪 Testing Message Generator\n")
        
        # Test connection request
        print("=" * 60)
        print("CONNECTION REQUEST MESSAGES")
        print("=" * 60)
        
        messages = generator.generate_connection_request(
            lead_name="Sarah Johnson",
            lead_title="Marketing Director",
            lead_company="TechCorp Inc",
            persona_name="Marketing Agencies"
        )
        
        for variant, message in messages.items():
            print(f"\n{variant.upper()}:")
            print(f"{message}")
            print(f"(Length: {len(message)} chars)")
        
        # Test follow-up
        print("\n" + "=" * 60)
        print("FOLLOW-UP MESSAGE 1")
        print("=" * 60)
        
        followup = generator.generate_follow_up_message(
            lead_name="Sarah Johnson",
            lead_title="Marketing Director",
            lead_company="TechCorp Inc",
            message_number=1
        )
        
        for variant, message in followup.items():
            print(f"\n{variant.upper()}:")
            print(f"{message}")
            print(f"(Length: {len(message)} chars)")
    
    elif args.lead_id:
        # Generate for specific lead
        messages = generator.generate_all_messages(lead_id=args.lead_id, save_to_db=True)
        
        print("\n" + "=" * 60)
        print("ALL MESSAGES GENERATED")
        print("=" * 60)
        
        for message_type, variants in messages.items():
            print(f"\n{message_type.upper().replace('_', ' ')}:")
            for variant, message in variants.items():
                print(f"  {variant}: {message[:100]}...")
    
    else:
        print("Usage:")
        print("  python message_generator.py --test")
        print("  python message_generator.py --lead-id 1")