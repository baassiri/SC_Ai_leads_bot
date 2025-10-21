"""
SC AI Lead Generation System - Persona Parser
Parse target persona data from Targets.docx file
"""

import sys
from pathlib import Path
from typing import List, Dict
import re

from docx import Document

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config
from backend.database.db_manager import db_manager


class PersonaParser:
    """Parse persona data from Word documents"""
    
    def __init__(self, docx_path: str = None):
        """
        Initialize persona parser
        
        Args:
            docx_path: Path to Targets.docx file
        """
        if docx_path:
            self.docx_path = Path(docx_path)
        else:
            # Default to uploads directory
            self.docx_path = Config.UPLOAD_DIR / 'Targets.docx'
        
        self.personas = []
    
    def parse_document(self) -> List[Dict]:
        """
        Parse the entire document and extract personas
        
        Returns:
            List[Dict]: List of persona dictionaries
        """
        try:
            print(f"\n📄 Parsing document: {self.docx_path}")
            
            if not self.docx_path.exists():
                print(f"❌ File not found: {self.docx_path}")
                return []
            
            # Load document
            doc = Document(str(self.docx_path))
            
            # Extract all text
            full_text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    full_text.append(paragraph.text.strip())
            
            print(f"  → Loaded {len(full_text)} paragraphs")
            
            # Parse personas
            self.personas = self.extract_personas(full_text)
            
            print(f"✅ Found {len(self.personas)} personas")
            
            return self.personas
            
        except Exception as e:
            print(f"❌ Error parsing document: {str(e)}")
            return []
    
    def extract_personas(self, text_lines: List[str]) -> List[Dict]:
        """
        Extract persona data from text lines
        
        Args:
            text_lines: List of text lines from document
            
        Returns:
            List[Dict]: Extracted personas
        """
        personas = []
        
        # Keywords to identify persona sections
        persona_keywords = [
            'plastic surgeon',
            'dermatologist',
            'med spa',
            'day spa',
            'wellness center',
            'aesthetic clinic'
        ]
        
        current_persona = None
        current_section = None
        
        for line in text_lines:
            line_lower = line.lower()
            
            # Check if this line starts a new persona
            for keyword in persona_keywords:
                if keyword in line_lower and (
                    line_lower.startswith(keyword) or 
                    line_lower.startswith('persona') or
                    line_lower.startswith('target') or
                    line_lower.startswith('#') or
                    len(line.split()) <= 5
                ):
                    # Save previous persona
                    if current_persona:
                        personas.append(current_persona)
                    
                    # Start new persona
                    current_persona = self.create_persona_template(line)
                    current_section = None
                    break
            
            # If we have a current persona, parse its sections
            if current_persona:
                # Identify section headers
                if any(kw in line_lower for kw in ['age', 'demographic']):
                    current_section = 'demographics'
                elif any(kw in line_lower for kw in ['goal', 'objective', 'want']):
                    current_section = 'goals'
                elif any(kw in line_lower for kw in ['pain', 'challenge', 'problem', 'struggle']):
                    current_section = 'pain_points'
                elif any(kw in line_lower for kw in ['message', 'positioning', 'value prop']):
                    current_section = 'messaging'
                elif any(kw in line_lower for kw in ['tone', 'style', 'voice']):
                    current_section = 'tone'
                
                # Add content to current section
                elif current_section and line.strip() and not line.startswith('#'):
                    self.add_to_section(current_persona, current_section, line)
        
        # Don't forget the last persona
        if current_persona:
            personas.append(current_persona)
        
        # If no personas found, return hardcoded defaults
        if not personas:
            print("  ⚠️ No personas detected in document, using defaults...")
            personas = self.get_default_personas()
        
        return personas
    
    def create_persona_template(self, title_line: str) -> Dict:
        """
        Create a persona template from title line
        
        Args:
            title_line: Line containing persona name
            
        Returns:
            Dict: Persona template
        """
        # Extract persona name
        name = self.extract_persona_name(title_line)
        
        # Determine description based on name
        descriptions = {
            'Plastic Surgeon': 'The Prestige Provider',
            'Dermatologist': 'The Clinical Authority',
            'Med Spa Owner': 'The Growth Seeker',
            'Day Spa': 'The Relaxation Brand Builder',
            'Wellness Center': 'The Holistic Healer',
            'Aesthetic Clinic': 'General Cosmetic Practice'
        }
        
        return {
            'name': name,
            'description': descriptions.get(name, 'Healthcare Professional'),
            'age_range': '',
            'gender_distribution': '',
            'goals': '',
            'pain_points': '',
            'key_message': '',
            'message_tone': ''
        }
    
    def extract_persona_name(self, line: str) -> str:
        """Extract persona name from line"""
        line_lower = line.lower()
        
        if 'plastic surgeon' in line_lower:
            return 'Plastic Surgeon'
        elif 'dermatologist' in line_lower:
            return 'Dermatologist'
        elif 'med spa' in line_lower or 'medspa' in line_lower:
            return 'Med Spa Owner'
        elif 'day spa' in line_lower:
            return 'Day Spa'
        elif 'wellness' in line_lower:
            return 'Wellness Center'
        elif 'aesthetic' in line_lower or 'cosmetic' in line_lower:
            return 'Aesthetic Clinic'
        else:
            # Extract capitalized words as name
            words = [w for w in line.split() if w[0].isupper()]
            return ' '.join(words[:3]) if words else 'Unknown Persona'
    
    def add_to_section(self, persona: Dict, section: str, content: str):
        """Add content to persona section"""
        content = content.strip()
        
        if not content:
            return
        
        # Remove bullet points and numbering
        content = re.sub(r'^[\d\.\-\*•]+\s*', '', content)
        
        # Map sections to persona fields
        section_map = {
            'demographics': ['age_range', 'gender_distribution'],
            'goals': 'goals',
            'pain_points': 'pain_points',
            'messaging': 'key_message',
            'tone': 'message_tone'
        }
        
        field = section_map.get(section)
        
        if isinstance(field, list):
            # Demographics - try to parse age and gender
            if 'age' in content.lower() or any(c.isdigit() for c in content):
                if persona['age_range']:
                    persona['age_range'] += ' | ' + content
                else:
                    persona['age_range'] = content
            else:
                if persona['gender_distribution']:
                    persona['gender_distribution'] += ' | ' + content
                else:
                    persona['gender_distribution'] = content
        elif field:
            # Append to existing content
            if persona[field]:
                persona[field] += '\n' + content
            else:
                persona[field] = content
    
    def get_default_personas(self) -> List[Dict]:
        """Return default personas if document parsing fails"""
        return [
            {
                'name': 'Plastic Surgeon',
                'description': 'The Prestige Provider',
                'age_range': '40-65',
                'gender_distribution': 'Predominantly male (70-80%)',
                'goals': 'Attract high-value cosmetic cases, build strong regional reputation, fill schedule with elective procedures',
                'pain_points': 'Competing with med-spas offering cheaper treatments, inconsistent patient flow, website doesn\'t reflect premium brand',
                'key_message': 'Grow your reputation and patient bookings with proven digital systems built for plastic surgeons.',
                'message_tone': 'Consultative, prestige-focused, data-driven'
            },
            {
                'name': 'Dermatologist',
                'description': 'The Clinical Authority',
                'age_range': '35-60',
                'gender_distribution': 'Mix of male/female (60/40)',
                'goals': 'Balance medical and aesthetic revenue, increase bookings for injectables and lasers, enhance online visibility',
                'pain_points': 'Limited time for marketing, weak online reviews or local SEO, not converting enough cosmetic leads',
                'key_message': 'Expand your aesthetic revenue with results-driven marketing for dermatology practices.',
                'message_tone': 'Clinical authority, results-oriented, professional'
            },
            {
                'name': 'Med Spa Owner',
                'description': 'The Growth Seeker',
                'age_range': '30-55',
                'gender_distribution': 'Often female entrepreneurs (65%)',
                'goals': 'Consistent monthly bookings for injectables, scale brand awareness, automate client retention',
                'pain_points': 'High local competition, poor ad performance or tracking, weak branding or inconsistent visuals',
                'key_message': 'Dominate your local market with data-backed campaigns that turn browsers into loyal med-spa clients.',
                'message_tone': 'Growth-oriented, entrepreneurial, data-backed'
            },
            {
                'name': 'Day Spa',
                'description': 'The Relaxation Brand Builder',
                'age_range': '35-60',
                'gender_distribution': 'Mostly female ownership (75%)',
                'goals': 'Attract consistent appointments for wellness, improve Google and social visibility, retain clients through memberships',
                'pain_points': 'Low repeat-visit rates, inconsistent messaging, outdated website, competing with franchise spas',
                'key_message': 'Build a recognizable, trusted spa brand with targeted marketing and retention systems.',
                'message_tone': 'Brand-building, retention-focused, wellness-oriented'
            },
            {
                'name': 'Wellness Center',
                'description': 'The Holistic Healer',
                'age_range': '30-60',
                'gender_distribution': 'Integrative health practitioners (mix)',
                'goals': 'Promote wellness packages, educate clients on long-term benefits, build steady digital leads',
                'pain_points': 'Hard to communicate full service scope online, weak SEO or content strategy',
                'key_message': 'Position your wellness brand as the trusted destination for holistic health and beauty transformation.',
                'message_tone': 'Holistic, educational, long-term focused'
            },
            {
                'name': 'Aesthetic Clinic',
                'description': 'General Cosmetic Practice',
                'age_range': '30-65',
                'gender_distribution': 'Mixed (50/50)',
                'goals': 'Increase patient bookings, improve brand visibility, generate consistent qualified leads',
                'pain_points': 'Competition with specialized practices, difficulty differentiating services, inconsistent lead flow',
                'key_message': 'Grow your aesthetic practice with comprehensive digital marketing strategies.',
                'message_tone': 'Professional, growth-focused, comprehensive'
            }
        ]
    
    def save_to_database(self) -> int:
        """
        Save parsed personas to database
        
        Returns:
            int: Number of personas saved
        """
        if not self.personas:
            print("⚠️ No personas to save")
            return 0
        
        print(f"\n💾 Saving {len(self.personas)} personas to database...")
        
        saved_count = 0
        for persona in self.personas:
            try:
                # Check if persona already exists
                existing = db_manager.get_persona_by_name(persona['name'])
                
                if existing:
                    print(f"  ⚠️ Persona '{persona['name']}' already exists, skipping...")
                    continue
                
                # Create persona
                persona_id = db_manager.create_persona(
                    name=persona['name'],
                    description=persona.get('description'),
                    age_range=persona.get('age_range'),
                    gender_distribution=persona.get('gender_distribution'),
                    goals=persona.get('goals'),
                    pain_points=persona.get('pain_points'),
                    key_message=persona.get('key_message'),
                    message_tone=persona.get('message_tone')
                )
                
                if persona_id:
                    print(f"  ✅ Saved: {persona['name']}")
                    saved_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error saving {persona['name']}: {str(e)}")
        
        print(f"\n✅ Successfully saved {saved_count} personas")
        return saved_count
    
    def print_personas(self):
        """Print parsed personas for review"""
        if not self.personas:
            print("⚠️ No personas to display")
            return
        
        print("\n" + "="*60)
        print("📋 Parsed Personas")
        print("="*60)
        
        for i, persona in enumerate(self.personas, 1):
            print(f"\n{i}. {persona['name']} - {persona['description']}")
            print(f"   Age Range: {persona.get('age_range', 'N/A')}")
            print(f"   Gender: {persona.get('gender_distribution', 'N/A')}")
            print(f"   Goals: {persona.get('goals', 'N/A')[:100]}...")
            print(f"   Pain Points: {persona.get('pain_points', 'N/A')[:100]}...")
            print(f"   Tone: {persona.get('message_tone', 'N/A')}")
        
        print("\n" + "="*60)
    # For lead_routes.py - ADD THIS TO THE END:
    def register_lead_routes(app, db_manager):
        """Register lead routes blueprint"""
        app.register_blueprint(lead_routes)
        print("✅ Lead routes registered")


    # For message_routes.py - ADD THIS TO THE END:
    def register_message_routes(app, db_manager):
        """Register message routes blueprint"""
        app.register_blueprint(message_routes)
        print("✅ Message routes registered")

# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Persona Parser for Targets.docx')
    parser.add_argument('--file', type=str, help='Path to Targets.docx file')
    parser.add_argument('--save', action='store_true', help='Save to database')
    parser.add_argument('--print', action='store_true', help='Print parsed personas')
    
    args = parser.parse_args()
    
    # Create parser
    persona_parser = PersonaParser(docx_path=args.file)
    
    # Parse document
    personas = persona_parser.parse_document()
    
    # Print if requested
    if args.print:
        persona_parser.print_personas()
    
    # Save if requested
    if args.save:
        persona_parser.save_to_database()
    
    print(f"\n✅ Parsing complete! Found {len(personas)} personas")