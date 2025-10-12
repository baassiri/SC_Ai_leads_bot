"""
SC AI Lead Generation System - AI Persona Analyzer
Uses OpenAI to analyze uploaded documents and extract targeting criteria
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

from docx import Document
from openai import OpenAI

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config


class PersonaAnalyzer:
    """Analyze target persona documents using OpenAI"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize persona analyzer
        
        Args:
            openai_api_key: OpenAI API key (defaults to config)
        """
        self.api_key = openai_api_key or Config.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extract all text from a .docx file
        
        Args:
            docx_path: Path to .docx file
            
        Returns:
            str: Extracted text
        """
        try:
            doc = Document(docx_path)
            
            # Extract all paragraphs
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            # Extract tables too
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
    
    def analyze_personas(self, document_text: str) -> Dict:
        """
        Use OpenAI to analyze the document and extract targeting criteria
        
        Args:
            document_text: Full text content from document
            
        Returns:
            Dict: Structured persona data
        """
        print("\n🤖 Asking OpenAI to analyze the document...")
        
        prompt = f"""
You are an expert at analyzing target customer personas and extracting LinkedIn search criteria.

I will give you a document describing target client personas. Your job is to:

1. Identify ALL personas/customer types mentioned
2. Extract key job titles and roles to search for on LinkedIn
3. Identify industries and company types
4. Extract keywords for LinkedIn search
5. Understand their pain points and goals

**Document Content:**
{document_text}

**Please respond with a JSON object in this EXACT format:**
{{
  "personas": [
    {{
      "name": "Persona name (e.g., 'Agency Owner', 'Marketing Director')",
      "description": "Brief description",
      "job_titles": ["Title 1", "Title 2", "Title 3"],
      "industries": ["Industry 1", "Industry 2"],
      "company_types": ["Type 1", "Type 2"],
      "pain_points": ["Pain 1", "Pain 2"],
      "goals": ["Goal 1", "Goal 2"],
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ],
  "linkedin_search_query": "Complete LinkedIn search query using OR operators",
  "primary_titles": ["Most important job titles to search"],
  "primary_industries": ["Most relevant industries"]
}}

**CRITICAL:** Return ONLY valid JSON. No explanation, no markdown, just pure JSON.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a LinkedIn lead generation expert. You analyze target personas and generate precise search criteria. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract response
            ai_response = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if ai_response.startswith('```'):
                ai_response = ai_response.split('```')[1]
                if ai_response.startswith('json'):
                    ai_response = ai_response[4:]
                ai_response = ai_response.strip()
            
            # Parse JSON
            result = json.loads(ai_response)
            
            print(f"✅ OpenAI analyzed document successfully!")
            print(f"   Found {len(result.get('personas', []))} personas")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {str(e)}")
            print(f"   Raw response: {ai_response[:200]}...")
            return self._get_fallback_analysis()
            
        except Exception as e:
            print(f"❌ Error calling OpenAI: {str(e)}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> Dict:
        """Return a basic fallback structure if OpenAI fails"""
        return {
            "personas": [],
            "linkedin_search_query": "",
            "primary_titles": [],
            "primary_industries": []
        }
    
    def analyze_document(self, docx_path: str) -> Dict:
        """
        Main method: Analyze a document and return targeting criteria
        
        Args:
            docx_path: Path to .docx file
            
        Returns:
            Dict: Complete analysis results
        """
        print("\n" + "="*60)
        print("🎯 AI PERSONA ANALYZER - Starting Analysis")
        print("="*60)
        
        # Step 1: Extract text
        document_text = self.extract_text_from_docx(docx_path)
        
        if not document_text:
            print("❌ No text extracted from document")
            return self._get_fallback_analysis()
        
        # Step 2: Analyze with OpenAI
        analysis = self.analyze_personas(document_text)
        
        # Step 3: Display results
        self.print_analysis(analysis)
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Print analysis results in a readable format"""
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS")
        print("="*60)
        
        personas = analysis.get('personas', [])
        
        if not personas:
            print("⚠️  No personas found in analysis")
            return
        
        print(f"\n🎯 Found {len(personas)} Target Personas:\n")
        
        for i, persona in enumerate(personas, 1):
            print(f"{i}. {persona.get('name', 'Unknown')}")
            print(f"   Description: {persona.get('description', 'N/A')}")
            print(f"   Job Titles: {', '.join(persona.get('job_titles', [])[:3])}")
            print(f"   Industries: {', '.join(persona.get('industries', [])[:3])}")
            print(f"   Keywords: {', '.join(persona.get('keywords', [])[:5])}")
            print()
        
        print("\n🔍 LinkedIn Search Query:")
        print(f"   {analysis.get('linkedin_search_query', 'N/A')}")
        
        print("\n📋 Primary Job Titles to Search:")
        for title in analysis.get('primary_titles', []):
            print(f"   • {title}")
        
        print("\n🏢 Primary Industries:")
        for industry in analysis.get('primary_industries', []):
            print(f"   • {industry}")
        
        print("\n" + "="*60)


# Singleton instance
def create_analyzer(api_key: str = None) -> PersonaAnalyzer:
    """Factory function to create analyzer instance"""
    return PersonaAnalyzer(openai_api_key=api_key)


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Persona Analyzer')
    parser.add_argument('--file', type=str, required=True, help='Path to .docx file')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = create_analyzer(api_key=args.api_key)
    
    # Analyze document
    result = analyzer.analyze_document(args.file)
    
    # Save to JSON file
    output_path = Path(args.file).stem + '_analysis.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n💾 Analysis saved to: {output_path}")