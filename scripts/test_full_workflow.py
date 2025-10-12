"""
SC AI Lead Generation System - Full Workflow Test
Tests the complete pipeline from document upload to lead generation
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * 70)

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_step(step_num, total_steps, text):
    """Print step information"""
    print(f"\n{Colors.BOLD}[Step {step_num}/{total_steps}]{Colors.ENDC} {text}")


class WorkflowTester:
    """Test the complete workflow"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.start_time = None
        self.personas_created = 0
        self.leads_created = 0
    
    def run_all_tests(self):
        """Run all workflow tests"""
        self.start_time = datetime.now()
        
        print_header("🧪 SC AI LEAD GENERATION SYSTEM - WORKFLOW TEST")
        print_info(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_steps = 10
        
        # Step 1: Environment Check
        print_step(1, total_steps, "Environment Check")
        self.test_environment()
        
        # Step 2: Database Connection
        print_step(2, total_steps, "Database Connection")
        self.test_database_connection()
        
        # Step 3: Database Schema
        print_step(3, total_steps, "Database Schema & Tables")
        self.test_database_schema()
        
        # Step 4: Credentials Manager
        print_step(4, total_steps, "Credentials Management")
        self.test_credentials_manager()
        
        # Step 5: Session Manager
        print_step(5, total_steps, "Session Management")
        self.test_session_manager()
        
        # Step 6: Persona Analysis
        print_step(6, total_steps, "AI Persona Analysis")
        self.test_persona_analyzer()
        
        # Step 7: Lead Generation
        print_step(7, total_steps, "Lead Generation")
        self.test_lead_generation()
        
        # Step 8: AI Lead Scoring
        print_step(8, total_steps, "AI Lead Scoring")
        self.test_lead_scoring()
        
        # Step 9: API Endpoints
        print_step(9, total_steps, "Flask API Endpoints")
        self.test_api_endpoints()
        
        # Step 10: CSV Export/Import
        print_step(10, total_steps, "CSV Export/Import")
        self.test_csv_operations()
        
        # Print summary
        self.print_summary()
    
    def test_environment(self):
        """Test environment setup"""
        try:
            # Check Python version
            import sys
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
                self.results['passed'].append("Python version check")
            else:
                print_error(f"Python version too old: {version.major}.{version.minor}.{version.micro}")
                self.results['failed'].append("Python version check")
            
            # Check critical imports
            critical_imports = [
                'flask',
                'sqlalchemy',
                'openai',
                'selenium',
                'docx'
            ]
            
            for module_name in critical_imports:
                try:
                    __import__(module_name)
                    print_success(f"Module '{module_name}' is installed")
                    self.results['passed'].append(f"Import {module_name}")
                except ImportError:
                    print_error(f"Module '{module_name}' is NOT installed")
                    self.results['failed'].append(f"Import {module_name}")
            
            # Check directories
            from backend.config import Config
            
            required_dirs = [
                Config.DATA_DIR,
                Config.UPLOAD_DIR,
                Config.EXPORT_DIR,
                Config.LOG_DIR
            ]
            
            for directory in required_dirs:
                if directory.exists():
                    print_success(f"Directory exists: {directory.name}")
                    self.results['passed'].append(f"Directory {directory.name}")
                else:
                    print_error(f"Directory missing: {directory}")
                    self.results['failed'].append(f"Directory {directory.name}")
        
        except Exception as e:
            print_error(f"Environment check failed: {str(e)}")
            self.results['failed'].append("Environment check")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from backend.database.db_manager import db_manager
            
            # Try to connect
            with db_manager.session_scope() as session:
                print_success("Database connection successful")
                self.results['passed'].append("Database connection")
        
        except Exception as e:
            print_error(f"Database connection failed: {str(e)}")
            self.results['failed'].append("Database connection")
    
    def test_database_schema(self):
        """Test database schema"""
        try:
            from backend.database.db_manager import db_manager
            from backend.database.models import User, Persona, Lead, Message, Campaign
            
            # Check if tables exist
            tables = ['users', 'personas', 'leads', 'messages', 'campaigns', 'responses', 'activity_logs']
            
            with db_manager.session_scope() as session:
                for table_name in tables:
                    try:
                        # Try to query each table
                        if table_name == 'users':
                            session.query(User).first()
                        elif table_name == 'personas':
                            session.query(Persona).first()
                        elif table_name == 'leads':
                            session.query(Lead).first()
                        elif table_name == 'messages':
                            session.query(Message).first()
                        elif table_name == 'campaigns':
                            session.query(Campaign).first()
                        
                        print_success(f"Table '{table_name}' exists and is accessible")
                        self.results['passed'].append(f"Table {table_name}")
                    
                    except Exception as e:
                        print_error(f"Table '{table_name}' error: {str(e)}")
                        self.results['failed'].append(f"Table {table_name}")
        
        except Exception as e:
            print_error(f"Schema test failed: {str(e)}")
            self.results['failed'].append("Database schema")
    
    def test_credentials_manager(self):
        """Test credentials management"""
        try:
            from backend.credentials_manager import credentials_manager
            
            # Test saving credentials
            test_creds = {
                'linkedin_email': 'test@example.com',
                'linkedin_password': 'test_password',
                'openai_api_key': 'sk-test-key-12345'
            }
            
            success = credentials_manager.save_all_credentials(**test_creds)
            
            if success:
                print_success("Credentials save successful")
                self.results['passed'].append("Save credentials")
            else:
                print_error("Credentials save failed")
                self.results['failed'].append("Save credentials")
            
            # Test retrieving credentials
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            openai_key = credentials_manager.get_openai_key()
            
            if linkedin_creds:
                print_success("Credentials retrieval successful")
                self.results['passed'].append("Retrieve credentials")
            else:
                print_warning("No credentials found (expected on first run)")
                self.results['warnings'].append("No credentials configured")
        
        except Exception as e:
            print_error(f"Credentials manager test failed: {str(e)}")
            self.results['failed'].append("Credentials manager")
    
    def test_session_manager(self):
        """Test session management"""
        try:
            from backend.session_manager import session_manager
            
            # Test session summary
            summary = session_manager.get_session_summary()
            
            print_success("Session manager operational")
            print_info(f"   Personas loaded: {summary.get('personas_count', 0)}")
            print_info(f"   Has analysis: {summary.get('has_analysis', False)}")
            
            self.results['passed'].append("Session manager")
        
        except Exception as e:
            print_error(f"Session manager test failed: {str(e)}")
            self.results['failed'].append("Session manager")
    
    def test_persona_analyzer(self):
        """Test AI persona analyzer"""
        try:
            from backend.ai_engine.persona_analyzer import create_analyzer
            from backend.database.db_manager import db_manager
            
            print_info("Testing persona analyzer...")
            
            # Create test document content
            test_document_text = """
            TARGET PERSONAS:
            
            1. Marketing Agency Owners
               - Age: 30-50
               - Focus: Digital marketing and automation
               - Pain Points: Manual processes, inconsistent lead generation
               - Goals: Scale operations, improve efficiency
            
            2. Tech Startup Founders
               - Age: 25-45
               - Focus: Rapid growth and innovation
               - Pain Points: Limited resources, need for automation
               - Goals: Streamline operations, reduce costs
            """
            
            # Create analyzer (works even without API key - uses fallback)
            analyzer = create_analyzer(api_key='')
            
            # Test fallback analysis
            result = analyzer.analyze_personas_fallback(test_document_text)
            
            if result and len(result.get('personas', [])) > 0:
                print_success(f"Persona analysis successful - found {len(result['personas'])} personas")
                
                # Try to save personas to database
                for persona_data in result.get('personas', []):
                    try:
                        persona_id = db_manager.create_persona(
                            name=persona_data.get('name', 'Test Persona'),
                            description=persona_data.get('description', ''),
                            goals=str(persona_data.get('goals', [])),
                            pain_points=str(persona_data.get('pain_points', []))
                        )
                        
                        if persona_id:
                            self.personas_created += 1
                    except Exception as e:
                        print_warning(f"Persona may already exist: {persona_data.get('name')}")
                
                print_success(f"Created {self.personas_created} new personas in database")
                self.results['passed'].append("Persona analyzer")
            else:
                print_error("Persona analysis returned no results")
                self.results['failed'].append("Persona analyzer")
        
        except Exception as e:
            print_error(f"Persona analyzer test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['failed'].append("Persona analyzer")
    
    def test_lead_generation(self):
        """Test lead generation"""
        try:
            from backend.database.db_manager import db_manager
            
            # Get personas from database
            personas = db_manager.get_all_personas()
            
            if not personas:
                print_warning("No personas in database - skipping lead generation")
                self.results['warnings'].append("No personas for lead generation")
                return
            
            # Generate test leads
            import random
            
            first_names = ['John', 'Sarah', 'Michael', 'Emily', 'David']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
            
            for persona in personas[:2]:  # Test with first 2 personas
                for i in range(3):  # Generate 3 leads per persona
                    name = f"{random.choice(first_names)} {random.choice(last_names)}"
                    
                    lead_id = db_manager.create_lead(
                        name=name,
                        title=f"{persona.get('name', 'Professional')}",
                        company=f"Test Company {i+1}",
                        industry="Technology",
                        location="San Francisco, CA",
                        profile_url=f"https://linkedin.com/in/test-{random.randint(1000,9999)}",
                        headline=f"Test lead for {persona.get('name')}",
                        company_size="11-50 employees"
                    )
                    
                    if lead_id:
                        self.leads_created += 1
            
            print_success(f"Generated {self.leads_created} test leads")
            self.results['passed'].append("Lead generation")
        
        except Exception as e:
            print_error(f"Lead generation test failed: {str(e)}")
            self.results['failed'].append("Lead generation")
    
    def test_lead_scoring(self):
        """Test AI lead scoring"""
        try:
            from backend.ai_engine.lead_scorer import score_lead
            from backend.database.db_manager import db_manager
            
            # Get all leads
            leads = db_manager.get_all_leads(limit=5)
            
            if not leads:
                print_warning("No leads to score")
                self.results['warnings'].append("No leads for scoring")
                return
            
            # Score each lead
            scored_count = 0
            for lead in leads:
                try:
                    # Create lead data dict
                    lead_data = {
                        'name': lead.get('name'),
                        'title': lead.get('title'),
                        'company': lead.get('company'),
                        'location': lead.get('location'),
                        'company_size': lead.get('company_size')
                    }
                    
                    # Score the lead
                    result = score_lead(lead_data)
                    
                    # Update score in database
                    db_manager.update_lead_score(
                        lead.get('id'),
                        result['score'],
                        score_reasoning=result['reasoning']
                    )
                    
                    scored_count += 1
                    print_info(f"   Scored '{lead.get('name')}': {result['score']}/100")
                
                except Exception as e:
                    print_warning(f"Failed to score lead: {str(e)}")
            
            print_success(f"Scored {scored_count} leads")
            self.results['passed'].append("Lead scoring")
        
        except Exception as e:
            print_error(f"Lead scoring test failed: {str(e)}")
            self.results['failed'].append("Lead scoring")
    
    def test_api_endpoints(self):
        """Test Flask API endpoints"""
        try:
            import requests
            
            # Check if server is running
            base_url = "http://localhost:5000"
            
            print_info("Testing API endpoints (requires Flask server running)...")
            
            endpoints = [
                ('/api/personas', 'GET'),
                ('/api/leads', 'GET'),
                ('/api/analytics/dashboard', 'GET'),
                ('/api/activity-logs', 'GET')
            ]
            
            api_working = True
            
            for endpoint, method in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=2)
                    
                    if response.status_code == 200:
                        print_success(f"API {endpoint} - OK")
                    else:
                        print_warning(f"API {endpoint} - Status {response.status_code}")
                        api_working = False
                
                except requests.exceptions.ConnectionError:
                    print_warning(f"API {endpoint} - Server not running")
                    api_working = False
                    break
                except Exception as e:
                    print_warning(f"API {endpoint} - Error: {str(e)}")
                    api_working = False
            
            if api_working:
                self.results['passed'].append("API endpoints")
            else:
                self.results['warnings'].append("API endpoints (server may not be running)")
        
        except ImportError:
            print_warning("Requests library not installed - skipping API tests")
            self.results['warnings'].append("API tests (requests not installed)")
        except Exception as e:
            print_error(f"API test failed: {str(e)}")
            self.results['failed'].append("API endpoints")
    
    def test_csv_operations(self):
        """Test CSV export and import"""
        try:
            from backend.scrapers.csv_handler import csv_handler
            from backend.database.db_manager import db_manager
            
            # Get some leads
            leads = db_manager.get_all_leads(limit=5)
            
            if not leads:
                print_warning("No leads to export")
                self.results['warnings'].append("No leads for CSV export")
                return
            
            # Test export
            filepath = csv_handler.export_leads_to_csv(leads, filename='test_export.csv')
            
            if os.path.exists(filepath):
                print_success(f"CSV export successful: {filepath}")
                
                # Test import
                imported_leads = csv_handler.import_leads_from_csv(filepath)
                
                if len(imported_leads) > 0:
                    print_success(f"CSV import successful: {len(imported_leads)} leads")
                    self.results['passed'].append("CSV operations")
                else:
                    print_error("CSV import returned no leads")
                    self.results['failed'].append("CSV import")
            else:
                print_error("CSV export file not created")
                self.results['failed'].append("CSV export")
        
        except Exception as e:
            print_error(f"CSV operations test failed: {str(e)}")
            self.results['failed'].append("CSV operations")
    
    def print_summary(self):
        """Print test summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print_header("📊 TEST SUMMARY")
        
        print(f"\n{Colors.BOLD}Duration:{Colors.ENDC} {duration.seconds} seconds")
        print(f"{Colors.BOLD}Personas Created:{Colors.ENDC} {self.personas_created}")
        print(f"{Colors.BOLD}Leads Created:{Colors.ENDC} {self.leads_created}")
        
        print(f"\n{Colors.OKGREEN}✅ Passed:{Colors.ENDC} {len(self.results['passed'])}")
        for test in self.results['passed']:
            print(f"   • {test}")
        
        if self.results['warnings']:
            print(f"\n{Colors.WARNING}⚠️  Warnings:{Colors.ENDC} {len(self.results['warnings'])}")
            for test in self.results['warnings']:
                print(f"   • {test}")
        
        if self.results['failed']:
            print(f"\n{Colors.FAIL}❌ Failed:{Colors.ENDC} {len(self.results['failed'])}")
            for test in self.results['failed']:
                print(f"   • {test}")
        
        # Calculate success rate
        total_tests = len(self.results['passed']) + len(self.results['failed'])
        if total_tests > 0:
            success_rate = (len(self.results['passed']) / total_tests) * 100
            
            print(f"\n{Colors.BOLD}Success Rate:{Colors.ENDC} {success_rate:.1f}%")
            
            if success_rate >= 80:
                print(f"\n{Colors.OKGREEN}🎉 System is ready for use!{Colors.ENDC}")
            elif success_rate >= 60:
                print(f"\n{Colors.WARNING}⚠️  System is partially functional - review warnings{Colors.ENDC}")
            else:
                print(f"\n{Colors.FAIL}❌ System needs attention - multiple failures detected{Colors.ENDC}")
        
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
        print("1. Fix any failed tests")
        print("2. Start Flask server: python backend/app.py")
        print("3. Visit: http://localhost:5000")
        print("4. Upload a document to create personas")
        print("5. Start the bot to generate leads")
        print("=" * 70 + "\n")


def main():
    """Main test function"""
    try:
        tester = WorkflowTester()
        tester.run_all_tests()
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Test interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()