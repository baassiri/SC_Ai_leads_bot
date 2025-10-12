"""
SC AI Lead Generation System - AI Persona Analyzer (IMPROVED)
Uses OpenAI to analyze uploaded documents - with fallback if API fails
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

from docx import Document

# Try to import OpenAI - gracefully handle if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("⚠️  OpenAI library not installed")
    OPENAI_AVAILABLE = False

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config


class PersonaAnalyzer:
    """Analyze target persona documents using OpenAI (with fallback)"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize persona analyzer
        
        Args:
            openai_api_key: OpenAI API key (defaults to config)
        """
        self.api_key = openai_api_key or Config.OPENAI_API_KEY
        self.client = None
        
        if not OPENAI_AVAILABLE:
            print("⚠️  OpenAI library not available - using fallback parser")
            return
        
        if not self.api_key or self.api_key == '' or self.api_key == 'sk-your-openai-api-key-here':
            print("⚠️  WARNING: No valid OpenAI API key configured!")
            print("   Using fallback rule-based persona extraction")
            print("   💡 Add your API key at: http://localhost:5000/")
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
                print(f"🔑 OpenAI client initialized (key: ...{self.api_key[-4:]})")
            except Exception as e:
                print(f"⚠️  Error initializing OpenAI: {str(e)}")
                print("   Using fallback parser instead")
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract all text from a .docx file"""
        try:
            doc = Document(docx_path)
            
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text.strip())
            
            full_text = '\n'.join(text_content)
            print(f"✅ Extracted {len(full_text)} characters from document")
            
            return full_text
            
        except Exception as e:
            print(f"❌ Error extracting text: {str(e)}")
            return ""
    
    def analyze_personas_with_ai(self, document_text: str) -> Dict:
        """Use OpenAI to analyze the document"""
        print("\n🤖 Asking OpenAI to analyze the document...")
        
        prompt = f"""
You are an expert at analyzing target customer personas and extracting LinkedIn search criteria.

Analyze this document and identify ALL personas/customer types mentioned.

**Document:**
{document_text[:3000]}

**Respond with valid JSON only:**
{{
  "personas": [
    {{
      "name": "Persona name",
      "description": "Brief description",
      "job_titles": ["Title 1", "Title 2"],
      "industries": ["Industry 1"],
      "pain_points": ["Pain 1"],
      "goals": ["Goal 1"],
      "keywords": ["keyword1", "keyword2"]
    }}
  ],
  "linkedin_search_query": "job title OR job title OR job title",
  "primary_titles": ["Most important titles"],
  "primary_industries": ["Industries"]
}}

Return ONLY valid JSON, no explanation.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a LinkedIn lead generation expert. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Clean response
            if ai_response.startswith('```'):
                ai_response = ai_response.split('```')[1]
                if ai_response.startswith('json'):
                    ai_response = ai_response[4:]
                ai_response = ai_response.strip()
            
            result = json.loads(ai_response)
            
            print(f"✅ AI analyzed successfully! Found {len(result.get('personas', []))} personas")
            
            return result
            
        except Exception as e:
            print(f"❌ OpenAI error: {str(e)}")
            return None
    
    def analyze_personas_fallback(self, document_text: str) -> Dict:
        """Fallback rule-based persona extraction"""
        print("\n📋 Using rule-based persona extraction...")
        
        text_lower = document_text.lower()
        
        # Define common healthcare/aesthetics personas
        persona_keywords = {
            'Plastic Surgeon': ['plastic surgeon', 'cosmetic surgeon', 'aesthetic surgeon'],
            'Dermatologist': ['dermatologist', 'dermatology', 'skin doctor'],
            'Med Spa Owner': ['med spa', 'medspa', 'medical spa', 'aesthetic clinic'],
            'Aesthetic Nurse': ['aesthetic nurse', 'cosmetic nurse', 'injector', 'nurse practitioner'],
            'Day Spa Owner': ['day spa', 'wellness spa', 'beauty spa'],
            'Wellness Center': ['wellness center', 'holistic health', 'integrative medicine']
        }
        
        # Detect which personas are mentioned
        found_personas = []
        all_titles = []
        
        for persona_name, keywords in persona_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_personas.append({
                        "name": persona_name,
                        "description": f"Healthcare professional in {persona_name.lower()} field",
                        "job_titles": [persona_name, keywords[0].title()],
                        "industries": ["Medical Practice", "Healthcare", "Wellness & Fitness"],
                        "pain_points": ["Need more clients", "Competition", "Marketing challenges"],
                        "goals": ["Grow practice", "Increase revenue", "Build reputation"],
                        "keywords": keywords[:3]
                    })
                    all_titles.extend([persona_name, keywords[0].title()])
                    break  # Only add once
        
        # If no specific personas found, use generic healthcare
        if not found_personas:
            print("⚠️  No specific personas detected, using generic healthcare professionals")
            found_personas = [
                {
                    "name": "Healthcare Professional",
                    "description": "General medical or wellness practitioner",
                    "job_titles": ["Doctor", "Physician", "Medical Director", "Practice Owner"],
                    "industries": ["Medical Practice", "Healthcare"],
                    "pain_points": ["Marketing challenges", "Patient acquisition"],
                    "goals": ["Grow practice", "Increase revenue"],
                    "keywords": ["doctor", "physician", "medical", "healthcare"]
                }
            ]
            all_titles = ["Doctor", "Physician", "Medical Director"]
        
        # Build LinkedIn search query
        linkedin_query = " OR ".join(f'"{title}"' for title in set(all_titles[:5]))
        
        result = {
            "personas": found_personas,
            "linkedin_search_query": linkedin_query,
            "primary_titles": list(set(all_titles[:8])),
            "primary_industries": ["Medical Practice", "Healthcare", "Wellness & Fitness"]
        }
        
        print(f"✅ Found {len(found_personas)} personas using fallback")
        
        return result
    
    def analyze_personas(self, document_text: str) -> Dict:
        """Analyze document - try AI first, fall back to rules"""
        # Try AI if available
        if self.client:
            result = self.analyze_personas_with_ai(document_text)
            if result and len(result.get('personas', [])) > 0:
                return result
            else:
                print("⚠️  AI returned empty results, trying fallback...")
        
        # Fall back to rule-based
        return self.analyze_personas_fallback(document_text)
    
    def analyze_document(self, docx_path: str) -> Dict:
        """Main method: Analyze a document and return targeting criteria"""
        print("\n" + "="*60)
        print("🎯 AI PERSONA ANALYZER - Starting Analysis")
        print("="*60)
        
        # Extract text
        document_text = self.extract_text_from_docx(docx_path)
        
        if not document_text:
            print("❌ No text extracted from document")
            return self.analyze_personas_fallback("")
        
        # Analyze with AI or fallback
        analysis = self.analyze_personas(document_text)
        
        # Display results
        self.print_analysis(analysis)
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Print analysis results"""
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        
        personas = analysis.get('personas', [])
        
        if not personas:
            print("⚠️  No personas found")
            return
        
        print(f"\n🎯 Found {len(personas)} Target Personas:\n")
        
        for i, persona in enumerate(personas, 1):
            print(f"{i}. {persona.get('name', 'Unknown')}")
            print(f"   Description: {persona.get('description', 'N/A')}")
            print(f"   Job Titles: {', '.join(persona.get('job_titles', [])[:3])}")
            print(f"   Keywords: {', '.join(persona.get('keywords', [])[:5])}")
            print()
        
        print("\n🔍 LinkedIn Search Query:")
        print(f"   {analysis.get('linkedin_search_query', 'N/A')}")
        
        print("\n" + "="*60)


# Factory function
def create_analyzer(api_key: str = None) -> PersonaAnalyzer:
    """Create analyzer instance"""
    return PersonaAnalyzer(openai_api_key=api_key)


if __name__ == '__main__':
    print("🧪 Testing Persona Analyzer")
    print("="*60)
    
    # Test with fallback (no API key)
    analyzer = create_analyzer(api_key="")
    
    # Create a test document
    test_text = """
    Target Personas:
    
    1. Plastic Surgeons - High-end cosmetic surgery practices
    2. Dermatologists - Medical and cosmetic dermatology
    3. Med Spa Owners - Aesthetic treatment centers
    """
    
    # Mock analyze
    result = analyzer.analyze_personas_fallback(test_text)
    analyzer.print_analysis(result)
    
    print("\n✅ Test complete!")