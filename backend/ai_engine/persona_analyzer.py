"""
Enhanced Persona Analyzer - Extracts EVERYTHING from target documents
Uses OpenAI GPT-4 to deeply understand persona documents and generate smart targeting
IMPROVED: Better error handling and fallback parsing
"""

from openai import OpenAI
import os
import re
import json
from typing import Dict, List, Any


class EnhancedPersonaAnalyzer:
    """
    Advanced persona extraction that captures:
    - Job titles and decision-maker roles
    - Pain points and challenges
    - Solutions offered
    - Key messaging
    - LinkedIn search keywords
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Deep analysis of persona document
        Returns structured data ready for scraping and messaging
        """
        
        # Read document
        text = self._read_document(file_path)
        
        print(f"📄 Document length: {len(text)} characters")
        
        prompt = f"""You are an expert at analyzing target customer documents for B2B lead generation.

Analyze this document and extract detailed information about target personas.

Document Content:
{text}

Extract and return a JSON object with this EXACT structure:

{{
  "personas": [
    {{
      "name": "Clear persona name (e.g. 'Agency Owner', 'Plastic Surgeon')",
      "description": "Brief 1-2 sentence description",
      
      "job_titles": [
        "Exact job titles to search on LinkedIn (e.g. 'CEO', 'Founder', 'Marketing Director')",
        "Include 5-10 specific titles that would appear on LinkedIn profiles"
      ],
      
      "decision_maker_roles": [
        "Roles that make purchasing decisions",
        "Include c-suite and management titles"
      ],
      
      "company_types": [
        "Types of companies they work at (e.g. 'Marketing Agency', 'SaaS Startup')",
        "Include industry categories"
      ],
      
      "pain_points": [
        "Specific problems they face",
        "Business challenges they need to solve",
        "Include 3-7 pain points"
      ],
      
      "solutions": [
        "Solutions/services that address their pain points",
        "Value propositions",
        "Include 3-7 solutions"
      ],
      
      "key_message": "Single powerful value proposition for this persona",
      
      "message_tone": "Professional tone description (e.g. 'Direct and data-driven', 'Warm and consultative')",
      
      "linkedin_keywords": [
        "Smart LinkedIn search keywords",
        "Combine job titles, industries, and role indicators",
        "Format for LinkedIn search (e.g. 'CEO founder startup', 'marketing director agency')",
        "Include 5-10 keyword combinations"
      ],
      
      "age_range": "Typical age range (e.g. '30-55')",
      
      "seniority_level": "Typical seniority (e.g. 'C-Suite', 'Director-level', 'Manager')"
    }}
  ],
  
  "industry_focus": "Primary industry or vertical from document",
  
  "service_offerings": [
    "Core services mentioned in document",
    "What is being sold to these personas"
  ],
  
  "common_hooks": [
    "Universal value propositions that work across personas",
    "Common pain points that all personas share"
  ]
}}

IMPORTANT RULES:
1. Extract REAL job titles that exist on LinkedIn
2. Make linkedin_keywords SPECIFIC - combine role + industry
3. Extract pain points verbatim when possible
4. Include key_message from document if present
5. If document has multiple personas, create separate entries for each
6. Be precise with job_titles - these will be used for LinkedIn searches

Return ONLY the JSON object, no other text."""

        try:
            print("🤖 Calling OpenAI GPT-4...")
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing target customer documents and extracting structured persona data. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            print(f"📥 Received response ({len(content)} chars)")
            print(f"First 200 chars: {content[:200]}")
            
            # Try multiple JSON extraction methods
            result = self._extract_json_from_response(content)
            
            if not result:
                print("⚠️ No valid JSON found, trying fallback extraction...")
                result = self._fallback_extraction(text)
            
            # Validate we have personas
            if not result.get('personas'):
                print("⚠️ No personas in result, trying fallback...")
                result = self._fallback_extraction(text)
            
            # Enrich personas with computed fields
            for persona in result.get('personas', []):
                # Generate smart search query
                persona['smart_search_query'] = self._generate_smart_search_query(persona)
                
                # Generate message hooks
                persona['message_hooks'] = self._generate_message_hooks(persona)
            
            print(f"✅ Successfully extracted {len(result.get('personas', []))} personas")
            
            return result
        
        except Exception as e:
            print(f"❌ Persona analysis error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Try fallback extraction
            print("🔄 Attempting fallback extraction...")
            try:
                result = self._fallback_extraction(text)
                print(f"✅ Fallback successful: {len(result.get('personas', []))} personas")
                return result
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                raise e
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Try multiple methods to extract JSON from GPT response"""
        
        # Method 1: Direct JSON parse
        try:
            return json.loads(content)
        except:
            pass
        
        # Method 2: Find JSON in markdown code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Method 3: Find any JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Method 4: Clean and retry
        try:
            # Remove markdown code blocks
            cleaned = re.sub(r'```json\s*', '', content)
            cleaned = re.sub(r'```\s*', '', cleaned)
            return json.loads(cleaned.strip())
        except:
            pass
        
        return None
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """
        Fallback: Extract personas using regex patterns
        When GPT fails to return proper JSON
        """
        print("🔍 Using pattern-based extraction...")
        
        personas = []
        
        # Look for persona sections
        persona_patterns = [
            r'(?:^|\n)(?:\d+\.\s*)?([A-Z][^:\n]+(?:Persona|Owner|Manager|Director|Surgeon|Consultant)[^:\n]*)',
            r'(?:^|\n)##?\s*(\d+\.\s*[A-Z][^\n]+Persona[^\n]*)',
        ]
        
        persona_names = []
        for pattern in persona_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            persona_names.extend(matches)
        
        # If we found persona headers, extract details for each
        if persona_names:
            print(f"   Found {len(persona_names)} persona headers")
            
            for name in persona_names[:10]:  # Limit to 10 personas
                # Clean the name
                name = re.sub(r'^\d+\.\s*', '', name).strip()
                name = re.sub(r'\s*--.*$', '', name).strip()  # Remove "-- The Something"
                
                # Extract job titles (look for titles near this persona)
                job_titles = self._extract_job_titles_near(text, name)
                
                # Extract pain points
                pain_points = self._extract_pain_points(text)
                
                # Extract solutions
                solutions = self._extract_solutions(text)
                
                persona = {
                    'name': name,
                    'description': f'Target persona from document: {name}',
                    'job_titles': job_titles or [name.split()[0]],  # Use first word as fallback
                    'decision_maker_roles': job_titles[:3] if job_titles else [name],
                    'company_types': [],
                    'pain_points': pain_points,
                    'solutions': solutions,
                    'key_message': f'Targeted solutions for {name}',
                    'message_tone': 'Professional and direct',
                    'linkedin_keywords': [name.replace(' Persona', '').replace(' Owner', '').strip()],
                    'age_range': '30-55',
                    'seniority_level': 'Executive'
                }
                
                personas.append(persona)
        
        # If still no personas, create generic ones
        if not personas:
            print("   No personas found, using document structure")
            personas = [{
                'name': 'Business Professional',
                'description': 'Target business professional from document',
                'job_titles': ['CEO', 'Founder', 'Director'],
                'decision_maker_roles': ['CEO', 'Founder'],
                'company_types': [],
                'pain_points': self._extract_pain_points(text),
                'solutions': self._extract_solutions(text),
                'key_message': 'Professional business solutions',
                'message_tone': 'Professional and direct',
                'linkedin_keywords': ['CEO', 'Founder', 'Director'],
                'age_range': '30-55',
                'seniority_level': 'Executive'
            }]
        
        result = {
            'personas': personas,
            'industry_focus': 'Professional Services',
            'service_offerings': self._extract_solutions(text),
            'common_hooks': []
        }
        
        return result
    
    def _extract_job_titles_near(self, text: str, persona_name: str) -> List[str]:
        """Extract job titles mentioned near a persona name"""
        titles = []
        
        # Common job title patterns
        title_patterns = [
            r'\b(CEO|CTO|CMO|CFO|COO)\b',
            r'\b(Founder|Co-Founder)\b',
            r'\b(Director|Manager|Head|Lead)\b',
            r'\b(Owner|Partner|Principal)\b',
            r'\b(Surgeon|Doctor|Physician)\b',
            r'\b(Consultant|Advisor|Coach)\b',
        ]
        
        # Find section with this persona
        persona_section = ''
        sections = text.split('\n\n')
        for i, section in enumerate(sections):
            if persona_name in section:
                # Get this section and next few
                persona_section = '\n'.join(sections[i:i+3])
                break
        
        if not persona_section:
            persona_section = text
        
        # Extract titles
        for pattern in title_patterns:
            matches = re.findall(pattern, persona_section, re.IGNORECASE)
            titles.extend([m.title() for m in matches])
        
        # Deduplicate
        return list(dict.fromkeys(titles))[:10]
    
    def _extract_pain_points(self, text: str) -> List[str]:
        """Extract pain points from document"""
        pain_points = []
        
        # Look for pain point sections
        pain_section_match = re.search(r'Pain\s+Points?\s*:?\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)', text, re.DOTALL | re.IGNORECASE)
        
        if pain_section_match:
            section = pain_section_match.group(1)
            # Extract bullet points or lines
            lines = re.findall(r'[-•·*]\s*(.+)', section)
            pain_points.extend([line.strip() for line in lines if len(line.strip()) > 10])
        
        return pain_points[:7]
    
    def _extract_solutions(self, text: str) -> List[str]:
        """Extract solutions from document"""
        solutions = []
        
        # Look for solution sections
        solution_patterns = [
            r'Solutions?\s+(?:You\s+)?Offer(?:ed)?\s*:?\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'Services?\s*:?\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
            r'Key\s+Message\s*:?\s*\n(.*?)(?:\n\n|\Z)'
        ]
        
        for pattern in solution_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section = match.group(1)
                lines = re.findall(r'[-•·*]\s*(.+)', section)
                solutions.extend([line.strip() for line in lines if len(line.strip()) > 10])
        
        return solutions[:7]
    
    def _read_document(self, file_path: str) -> str:
        """Read document content from file"""
        try:
            # Handle Word documents
            if file_path.endswith('.docx'):
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                return text
            
            # Handle text files
            elif file_path.endswith('.txt') or file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Handle PDF
            elif file_path.endswith('.pdf'):
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text() + '\n'
                    return text
            
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
        
        except Exception as e:
            print(f"Error reading document: {str(e)}")
            raise
    
    def _generate_smart_search_query(self, persona: Dict) -> str:
        """
        Generate optimized LinkedIn search query from persona data
        
        LinkedIn search works best with:
        - Job titles (CEO, founder, director)
        - Role indicators (marketing, operations, sales)
        - Industry terms (agency, startup, clinic)
        """
        
        # Get top job titles (most specific)
        job_titles = persona.get('job_titles', [])[:3]
        
        # Get company types
        company_types = persona.get('company_types', [])[:2]
        
        # Combine intelligently
        # Format: "title1 title2 OR title3 industry"
        if job_titles:
            query_parts = []
            
            # Add primary titles
            if len(job_titles) >= 2:
                query_parts.append(f"{job_titles[0]} {job_titles[1]}")
            elif len(job_titles) == 1:
                query_parts.append(job_titles[0])
            
            # Add industry context
            if company_types:
                # Extract key industry words (remove common words)
                industry_words = []
                for company_type in company_types:
                    words = company_type.lower().split()
                    meaningful_words = [w for w in words if len(w) > 3 and w not in ['company', 'companies', 'business']]
                    industry_words.extend(meaningful_words[:2])
                
                if industry_words:
                    query_parts.append(industry_words[0])
            
            return ' '.join(query_parts)
        
        # Fallback to linkedin_keywords
        keywords = persona.get('linkedin_keywords', [])
        if keywords:
            return keywords[0]
        
        # Last resort
        return persona.get('name', 'professional')
    
    def _generate_message_hooks(self, persona: Dict) -> List[str]:
        """
        Generate message hooks by pairing pain points with solutions
        """
        hooks = []
        
        pain_points = persona.get('pain_points', [])[:3]
        solutions = persona.get('solutions', [])[:3]
        
        # Create pain → solution hooks
        for i, pain in enumerate(pain_points):
            if i < len(solutions):
                hook = f"Struggling with {pain.lower()}? {solutions[i]}"
                hooks.append(hook)
        
        # Add key message as primary hook
        if persona.get('key_message'):
            hooks.insert(0, persona['key_message'])
        
        return hooks[:5]  # Max 5 hooks
    
    def extract_for_scraping(self, personas: List[Dict]) -> Dict[str, Any]:
        """
        Prepare persona data specifically for LinkedIn scraping
        Returns optimized search parameters
        """
        
        if not personas:
            return {
                'keywords': 'professional',
                'job_titles': [],
                'industries': []
            }
        
        # Aggregate all search data
        all_keywords = []
        all_job_titles = []
        all_industries = []
        
        for persona in personas:
            # Get smart search queries
            if persona.get('smart_search_query'):
                all_keywords.append(persona['smart_search_query'])
            
            # Get job titles
            all_job_titles.extend(persona.get('job_titles', [])[:5])
            
            # Get industries
            all_industries.extend(persona.get('company_types', [])[:3])
        
        # Deduplicate and prioritize
        unique_keywords = list(dict.fromkeys(all_keywords))[:5]
        unique_titles = list(dict.fromkeys(all_job_titles))[:10]
        unique_industries = list(dict.fromkeys(all_industries))[:5]
        
        return {
            'keywords': ' OR '.join(unique_keywords) if unique_keywords else unique_titles[0] if unique_titles else 'professional',
            'job_titles': unique_titles,
            'industries': unique_industries,
            'search_queries': unique_keywords
        }
    
    def extract_for_messaging(self, personas: List[Dict]) -> Dict[str, Any]:
        """
        Prepare persona data specifically for AI message generation
        Returns context for GPT prompts
        """
        
        messaging_context = {
            'personas': [],
            'universal_pain_points': [],
            'universal_solutions': [],
            'tone_guidelines': []
        }
        
        for persona in personas:
            persona_context = {
                'name': persona.get('name'),
                'pain_points': persona.get('pain_points', []),
                'solutions': persona.get('solutions', []),
                'key_message': persona.get('key_message'),
                'message_hooks': persona.get('message_hooks', []),
                'tone': persona.get('message_tone', 'Professional')
            }
            messaging_context['personas'].append(persona_context)
            
            # Aggregate universal elements
            messaging_context['universal_pain_points'].extend(persona.get('pain_points', [])[:2])
            messaging_context['universal_solutions'].extend(persona.get('solutions', [])[:2])
            
            if persona.get('message_tone'):
                messaging_context['tone_guidelines'].append(persona['message_tone'])
        
        # Deduplicate
        messaging_context['universal_pain_points'] = list(dict.fromkeys(messaging_context['universal_pain_points']))[:5]
        messaging_context['universal_solutions'] = list(dict.fromkeys(messaging_context['universal_solutions']))[:5]
        messaging_context['tone_guidelines'] = list(dict.fromkeys(messaging_context['tone_guidelines']))
        
        return messaging_context


# Factory function
def create_analyzer(api_key: str = None) -> EnhancedPersonaAnalyzer:
    """Create enhanced persona analyzer instance"""
    return EnhancedPersonaAnalyzer(api_key=api_key)


# CLI Test
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python persona_analyzer.py <document.txt>")
        sys.exit(1)
    
    analyzer = create_analyzer()
    result = analyzer.analyze_document(sys.argv[1])
    
    import json
    print(json.dumps(result, indent=2))
    
    print("\n" + "="*70)
    print("SCRAPING DATA:")
    print("="*70)
    scraping_data = analyzer.extract_for_scraping(result['personas'])
    print(json.dumps(scraping_data, indent=2))
    
    print("\n" + "="*70)
    print("MESSAGING DATA:")
    print("="*70)
    messaging_data = analyzer.extract_for_messaging(result['personas'])
    print(json.dumps(messaging_data, indent=2))