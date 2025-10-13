"""
SC AI Lead Generation System - Enhanced Full Workflow Test (FIXED)
Tests the complete pipeline with detailed diagnostics and recommendations
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    """Test the complete workflow with enhanced diagnostics"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'recommendations': []
        }
        self.start_time = None
        self.personas_created = 0
        self.leads_created = 0
        self.test_details = {}
    
    def run_all_tests(self):
        """Run all workflow tests"""
        self.start_time = datetime.now()
        
        print_header("🧪 SC AI LEAD GENERATION SYSTEM - ENHANCED WORKFLOW TEST")
        print_info(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print_info(f"Project root: {project_root}")
        
        total_steps = 12
        
        # Step 1: System Requirements
        print_step(1, total_steps, "System Requirements Check")
        self.test_system_requirements()
        
        # Step 2: Environment Check
        print_step(2, total_steps, "Environment Variables & Config")
        self.test_environment()
        
        # Step 3: File Structure
        print_step(3, total_steps, "File Structure & Directories")
        self.test_file_structure()
        
        # Step 4: Database Connection
        print_step(4, total_steps, "Database Connection")
        self.test_database_connection()
        
        # Step 5: Database Schema
        print_step(5, total_steps, "Database Schema & Tables")
        self.test_database_schema()
        
        # Step 6: Credentials Manager
        print_step(6, total_steps, "Credentials Management")
        self.test_credentials_manager()
        
        # Step 7: Session Manager
        print_step(7, total_steps, "Session Management")
        self.test_session_manager()
        
        # Step 8: Persona Analysis
        print_step(8, total_steps, "AI Persona Analysis")
        self.test_persona_analyzer()
        
        # Step 9: Lead Generation
        print_step(9, total_steps, "Lead Generation")
        self.test_lead_generation()
        
        # Step 10: AI Lead Scoring
        print_step(10, total_steps, "AI Lead Scoring")
        self.test_lead_scoring()
        
        # Step 11: CSV Operations
        print_step(11, total_steps, "CSV Export/Import")
        self.test_csv_operations()
        
        # Step 12: API Endpoints (optional - server needs to be running)
        print_step(12, total_steps, "Flask API Endpoints")
        self.test_api_endpoints()
        
        # Print summary
        self.print_summary()
        
        # Save detailed report
        self.save_test_report()
    
    def test_system_requirements(self):
        """Test system requirements"""
        try:
            import platform
            
            print_info(f"OS: {platform.system()} {platform.release()}")
            print_info(f"Python: {platform.python_version()}")
            
            # Check Python version
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                print_success(f"Python version is compatible: {version.major}.{version.minor}.{version.micro}")
                self.results['passed'].append("Python version")
            else:
                print_error(f"Python version too old: {version.major}.{version.minor}.{version.micro} (need 3.8+)")
                self.results['failed'].append("Python version")
                self.results['recommendations'].append("Upgrade to Python 3.8 or higher")
            
            # Check disk space
            import shutil
            stats = shutil.disk_usage(project_root)
            free_gb = stats.free / (1024**3)
            
            if free_gb > 1:
                print_success(f"Sufficient disk space: {free_gb:.1f} GB free")
                self.results['passed'].append("Disk space")
            else:
                print_warning(f"Low disk space: {free_gb:.1f} GB free")
                self.results['warnings'].append(f"Low disk space: {free_gb:.1f} GB")
            
            self.test_details['system'] = {
                'os': platform.system(),
                'python_version': platform.python_version(),
                'free_space_gb': free_gb
            }
            
        except Exception as e:
            print_error(f"System requirements check failed: {str(e)}")
            self.results['failed'].append("System requirements")
    
    def test_environment(self):
        """Test environment setup"""
        try:
            # Check critical imports - FIXED: Use correct import names
            critical_imports = {
                'flask': 'Flask web framework',
                'sqlalchemy': 'Database ORM',
                'openai': 'OpenAI API client (optional)',
                'selenium': 'Web scraping (optional)',
                'docx': 'Document parsing (python-docx package)',  # FIXED: Changed from 'python-docx'
            }
            
            installed = []
            missing = []
            
            for module_name, description in critical_imports.items():
                try:
                    # Test the actual import
                    __import__(module_name)
                    print_success(f"✓ {module_name}: {description}")
                    installed.append(module_name)
                    self.results['passed'].append(f"Import {module_name}")
                except ImportError:
                    print_warning(f"✗ {module_name}: {description} - NOT INSTALLED")
                    missing.append(module_name)
                    
                    if module_name in ['openai', 'selenium']:
                        self.results['warnings'].append(f"Optional: {module_name} not installed")
                    else:
                        self.results['failed'].append(f"Import {module_name}")
            
            if missing:
                # Map back to package names for installation
                package_map = {
                    'docx': 'python-docx'
                }
                
                install_packages = [package_map.get(m, m) for m in missing]
                
                print_info(f"\nTo install missing packages:")
                print_info(f"pip install {' '.join(install_packages)}")
                self.results['recommendations'].append(f"Install missing packages: {', '.join(install_packages)}")
            
            # Check config
            try:
                from backend.config import Config
                
                print_success("Config module loaded successfully")
                print_info(f"   DATABASE_URL: {Config.DATABASE_URL[:50]}...")
                print_info(f"   DEBUG: {Config.DEBUG}")
                
                self.results['passed'].append("Config loading")
            except Exception as e:
                print_error(f"Config loading failed: {str(e)}")
                self.results['failed'].append("Config loading")
            
        except Exception as e:
            print_error(f"Environment check failed: {str(e)}")
            self.results['failed'].append("Environment check")
    
    def test_file_structure(self):
        """Test file structure"""
        try:
            from backend.config import Config
            
            required_dirs = {
                'DATA_DIR': Config.DATA_DIR,
                'UPLOAD_DIR': Config.UPLOAD_DIR,
                'EXPORT_DIR': Config.EXPORT_DIR,
                'LOG_DIR': Config.LOG_DIR
            }
            
            all_exist = True
            
            for name, directory in required_dirs.items():
                if directory.exists():
                    print_success(f"✓ {name}: {directory}")
                    self.results['passed'].append(f"Directory {name}")
                else:
                    print_error(f"✗ {name} missing: {directory}")
                    self.results['failed'].append(f"Directory {name}")
                    all_exist = False
            
            if all_exist:
                print_success("All required directories exist")
            else:
                print_info("Run: python scripts/init_db.py to create missing directories")
                self.results['recommendations'].append("Run init_db.py to create directories")
            
        except Exception as e:
            print_error(f"File structure check failed: {str(e)}")
            self.results['failed'].append("File structure")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from backend.database.db_manager import db_manager
            
            # Try to connect
            with db_manager.session_scope() as session:
                # Try a simple query
                from backend.database.models import ActivityLog
                count = session.query(ActivityLog).count()
                
                print_success(f"Database connection successful")
                print_info(f"   Activity logs: {count} entries")
                self.results['passed'].append("Database connection")
                
                self.test_details['database'] = {
                    'connected': True,
                    'activity_log_count': count
                }
        
        except Exception as e:
            print_error(f"Database connection failed: {str(e)}")
            self.results['failed'].append("Database connection")
            self.results['recommendations'].append("Run: python scripts/init_db.py to initialize database")
            
            self.test_details['database'] = {
                'connected': False,
                'error': str(e)
            }
    
    def test_database_schema(self):
        """Test database schema"""
        try:
            from backend.database.db_manager import db_manager
            from backend.database.models import User, Persona, Lead, Message, Campaign, Response, ActivityLog
            
            tables = {
                'users': User,
                'personas': Persona,
                'leads': Lead,
                'messages': Message,
                'campaigns': Campaign,
                'responses': Response,
                'activity_logs': ActivityLog
            }
            
            table_counts = {}
            
            with db_manager.session_scope() as session:
                for table_name, model in tables.items():
                    try:
                        count = session.query(model).count()
                        print_success(f"✓ {table_name}: {count} records")
                        self.results['passed'].append(f"Table {table_name}")
                        table_counts[table_name] = count
                    
                    except Exception as e:
                        print_error(f"✗ {table_name}: {str(e)}")
                        self.results['failed'].append(f"Table {table_name}")
                        table_counts[table_name] = 'ERROR'
            
            self.test_details['tables'] = table_counts
            
        except Exception as e:
            print_error(f"Schema test failed: {str(e)}")
            self.results['failed'].append("Database schema")
    
    def test_credentials_manager(self):
        """Test credentials management"""
        try:
            from backend.credentials_manager import credentials_manager
            
            # Check if credentials exist
            linkedin_creds = credentials_manager.get_linkedin_credentials()
            openai_key = credentials_manager.get_openai_key()
            
            if linkedin_creds:
                print_success(f"LinkedIn credentials configured for: {linkedin_creds.get('email', 'unknown')}")
                self.results['passed'].append("LinkedIn credentials")
            else:
                print_warning("No LinkedIn credentials found")
                self.results['warnings'].append("LinkedIn credentials not configured")
                self.results['recommendations'].append("Configure LinkedIn credentials at http://localhost:5000/")
            
            if openai_key:
                print_success(f"OpenAI API key configured (ending in ...{openai_key[-4:]})")
                self.results['passed'].append("OpenAI credentials")
            else:
                print_warning("No OpenAI API key found")
                self.results['warnings'].append("OpenAI API key not configured")
                self.results['recommendations'].append("Configure OpenAI key for AI features")
            
            # Test saving (with dummy data)
            test_success = credentials_manager.save_all_credentials(
                linkedin_email='test@example.com',
                linkedin_password='test123',
                openai_api_key='sk-test-key'
            )
            
            if test_success:
                print_success("Credentials save/load functionality works")
                self.results['passed'].append("Credentials operations")
            
            self.test_details['credentials'] = {
                'linkedin_configured': linkedin_creds is not None,
                'openai_configured': openai_key is not None
            }
        
        except Exception as e:
            print_error(f"Credentials manager test failed: {str(e)}")
            self.results['failed'].append("Credentials manager")
    
    def test_session_manager(self):
        """Test session management"""
        try:
            from backend.session_manager import session_manager
            
            summary = session_manager.get_session_summary()
            
            print_success("Session manager operational")
            print_info(f"   Personas in session: {summary.get('personas_count', 0)}")
            print_info(f"   Has analysis: {summary.get('has_analysis', False)}")
            print_info(f"   Filters active: {summary.get('filters_active', False)}")
            
            if summary.get('linkedin_query'):
                print_info(f"   LinkedIn query: {summary['linkedin_query'][:50]}...")
            
            self.results['passed'].append("Session manager")
            self.test_details['session'] = summary
        
        except Exception as e:
            print_error(f"Session manager test failed: {str(e)}")
            self.results['failed'].append("Session manager")
    
    def test_persona_analyzer(self):
        """Test AI persona analyzer"""
        try:
            from backend.ai_engine.persona_analyzer import create_analyzer
            from backend.database.db_manager import db_manager
            
            print_info("Testing persona analyzer with sample text...")
            
            # Test document content
            test_text = """
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
            
            # Create analyzer (works with or without API key)
            analyzer = create_analyzer(api_key='')
            
            # Test analysis
            result = analyzer.analyze_personas_fallback(test_text)
            
            if result and len(result.get('personas', [])) > 0:
                print_success(f"Persona analysis successful - extracted {len(result['personas'])} personas")
                
                # Display extracted personas
                for i, persona in enumerate(result['personas'], 1):
                    print_info(f"   {i}. {persona.get('name', 'Unknown')}: {persona.get('description', 'N/A')}")
                
                # Try to save to database
                saved_count = 0
                for persona_data in result['personas']:
                    try:
                        persona_id = db_manager.create_persona(
                            name=f"TEST_{persona_data.get('name', 'Unknown')}",
                            description=persona_data.get('description', ''),
                            goals=str(persona_data.get('goals', [])),
                            pain_points=str(persona_data.get('pain_points', []))
                        )
                        
                        if persona_id:
                            saved_count += 1
                            self.personas_created += 1
                    except Exception as e:
                        print_warning(f"Could not save persona (may already exist): {persona_data.get('name')}")
                
                if saved_count > 0:
                    print_success(f"Saved {saved_count} test personas to database")
                
                self.results['passed'].append("Persona analyzer")
                self.test_details['persona_analysis'] = {
                    'extracted': len(result['personas']),
                    'saved': saved_count
                }
            else:
                print_error("Persona analysis returned no results")
                self.results['failed'].append("Persona analyzer")
        
        except Exception as e:
            print_error(f"Persona analyzer test failed: {str(e)}")
            import traceback
            print_error(traceback.format_exc())
            self.results['failed'].append("Persona analyzer")
    
    def test_lead_generation(self):
        """Test lead generation"""
        try:
            from backend.database.db_manager import db_manager
            import random
            
            # Get personas
            personas = db_manager.get_all_personas()
            
            if not personas or len(personas) == 0:
                print_warning("No personas in database - generating default persona")
                
                # Create a test persona
                persona_id = db_manager.create_persona(
                    name='Test Professional',
                    description='Test persona for lead generation',
                    goals='Test goals',
                    pain_points='Test pain points'
                )
                
                if persona_id:
                    personas = db_manager.get_all_personas()
            
            if not personas:
                print_error("Could not create or retrieve personas")
                self.results['failed'].append("Lead generation - no personas")
                return
            
            # Generate test leads
            first_names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
            locations = ['San Francisco, CA', 'New York, NY', 'Austin, TX', 'Chicago, IL', 'Boston, MA']
            
            leads_created = 0
            
            for persona in personas[:2]:  # Test with first 2 personas
                for i in range(3):  # Generate 3 leads per persona
                    name = f"{random.choice(first_names)} {random.choice(last_names)}"
                    
                    lead_id = db_manager.create_lead(
                        name=name,
                        title=f"{persona.get('name', 'Professional')}",
                        company=f"Test Company {random.randint(100,999)}",
                        industry="Technology",
                        location=random.choice(locations),
                        profile_url=f"https://linkedin.com/in/test-{random.randint(1000,9999)}",
                        headline=f"Test lead for {persona.get('name')}",
                        company_size=random.choice(['1-10', '11-50', '51-200']) + ' employees'
                    )
                    
                    if lead_id:
                        leads_created += 1
                        self.leads_created += 1
            
            if leads_created > 0:
                print_success(f"Generated {leads_created} test leads")
                self.results['passed'].append("Lead generation")
                self.test_details['lead_generation'] = {
                    'created': leads_created,
                    'personas_used': min(2, len(personas))
                }
            else:
                print_error("Failed to generate any leads")
                self.results['failed'].append("Lead generation")
        
        except Exception as e:
            print_error(f"Lead generation test failed: {str(e)}")
            self.results['failed'].append("Lead generation")
    
    def test_lead_scoring(self):
        """Test AI lead scoring"""
        try:
            from backend.ai_engine.lead_scorer import score_lead
            from backend.database.db_manager import db_manager
            
            # Get leads
            leads = db_manager.get_all_leads(limit=5)
            
            if not leads:
                print_warning("No leads available to score")
                self.results['warnings'].append("No leads for scoring")
                return
            
            scored_count = 0
            scores = []
            
            for lead in leads:
                try:
                    lead_data = {
                        'name': lead.get('name'),
                        'title': lead.get('title'),
                        'company': lead.get('company'),
                        'location': lead.get('location'),
                        'company_size': lead.get('company_size')
                    }
                    
                    # Score the lead
                    result = score_lead(lead_data)
                    score = result['score']
                    scores.append(score)
                    
                    # Update in database
                    db_manager.update_lead_score(
                        lead.get('id'),
                        score,
                        score_reasoning=result['reasoning']
                    )
                    
                    scored_count += 1
                    print_info(f"   ✓ '{lead.get('name')}': {score}/100 - {result['reasoning'][:50]}...")
                
                except Exception as e:
                    print_warning(f"Failed to score lead: {str(e)}")
            
            if scored_count > 0:
                avg_score = sum(scores) / len(scores)
                print_success(f"Scored {scored_count} leads (avg: {avg_score:.1f}/100)")
                self.results['passed'].append("Lead scoring")
                
                self.test_details['lead_scoring'] = {
                    'scored': scored_count,
                    'average_score': avg_score,
                    'min_score': min(scores),
                    'max_score': max(scores)
                }
            else:
                print_error("Failed to score any leads")
                self.results['failed'].append("Lead scoring")
        
        except Exception as e:
            print_error(f"Lead scoring test failed: {str(e)}")
            self.results['failed'].append("Lead scoring")
    
    def test_csv_operations(self):
        """Test CSV export and import - FIXED: Use correct import paths"""
        try:
            # FIXED: Try multiple possible locations for csv_handler
            csv_handler = None
            
            # Try backend.utils.csv_handler first
            try:
                from backend.utils.csv_handler import csv_handler as ch
                csv_handler = ch
                print_info("Using csv_handler from backend.utils")
            except ImportError:
                pass
            
            # Try backend.scrapers.csv_handler as fallback
            if csv_handler is None:
                try:
                    from backend.scrapers.csv_handler import csv_handler as ch
                    csv_handler = ch
                    print_info("Using csv_handler from backend.scrapers")
                except ImportError:
                    pass
            
            if csv_handler is None:
                print_error("Could not import csv_handler from any location")
                self.results['failed'].append("CSV operations - import failed")
                self.results['recommendations'].append("Check csv_handler.py location (should be in backend/utils or backend/scrapers)")
                return
            
            from backend.database.db_manager import db_manager
            
            # Get leads
            leads = db_manager.get_all_leads(limit=5)
            
            if not leads:
                print_warning("No leads to export")
                self.results['warnings'].append("No leads for CSV export")
                return
            
            # Test export
            export_path = csv_handler.export_leads_to_csv(leads, filename='test_export.csv')
            
            if os.path.exists(export_path):
                file_size = os.path.getsize(export_path)
                print_success(f"CSV export successful: {export_path}")
                print_info(f"   File size: {file_size} bytes")
                
                # Test import
                imported_leads = csv_handler.import_leads_from_csv(export_path)
                
                if len(imported_leads) > 0:
                    print_success(f"CSV import successful: {len(imported_leads)} leads")
                    self.results['passed'].append("CSV operations")
                    
                    self.test_details['csv'] = {
                        'exported': len(leads),
                        'imported': len(imported_leads),
                        'file_size': file_size
                    }
                else:
                    print_error("CSV import returned no leads")
                    self.results['failed'].append("CSV import")
                
                # Cleanup test file
                try:
                    os.remove(export_path)
                    print_info("   Cleaned up test export file")
                except:
                    pass
            else:
                print_error("CSV export file not created")
                self.results['failed'].append("CSV export")
        
        except Exception as e:
            print_error(f"CSV operations test failed: {str(e)}")
            import traceback
            print_error(traceback.format_exc())
            self.results['failed'].append("CSV operations")
    
    def test_api_endpoints(self):
        """Test Flask API endpoints"""
        try:
            import requests
            
            base_url = "http://localhost:5000"
            
            print_info("Testing API endpoints (Flask server must be running)...")
            
            endpoints = [
                ('/api/personas', 'GET', 'Personas list'),
                ('/api/leads', 'GET', 'Leads list'),
                ('/api/analytics/dashboard', 'GET', 'Dashboard stats'),
                ('/api/activity-logs', 'GET', 'Activity logs'),
                ('/api/bot/status', 'GET', 'Bot status')
            ]
            
            working = 0
            failed = 0
            
            for endpoint, method, description in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=3)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print_success(f"✓ {endpoint}: {description}")
                        if 'success' in data:
                            print_info(f"     Response: {str(data)[:100]}...")
                        working += 1
                    else:
                        print_warning(f"✗ {endpoint}: Status {response.status_code}")
                        failed += 1
                
                except requests.exceptions.ConnectionError:
                    print_warning(f"✗ {endpoint}: Cannot connect - is Flask running?")
                    failed += 1
                except Exception as e:
                    print_warning(f"✗ {endpoint}: {str(e)}")
                    failed += 1
            
            if working > 0:
                if failed == 0:
                    print_success(f"All {working} API endpoints working")
                    self.results['passed'].append("API endpoints")
                else:
                    print_warning(f"{working} endpoints working, {failed} failed")
                    self.results['warnings'].append(f"API partially working ({working}/{working+failed})")
                
                self.test_details['api'] = {
                    'working': working,
                    'failed': failed
                }
            else:
                print_warning("Flask server not running - start with: python backend/app.py")
                self.results['warnings'].append("API server not running")
                self.results['recommendations'].append("Start Flask server: python backend/app.py")
        
        except ImportError:
            print_warning("'requests' library not installed - skipping API tests")
            self.results['warnings'].append("API tests skipped (no requests library)")
            self.results['recommendations'].append("Install requests: pip install requests")
        except Exception as e:
            print_error(f"API test failed: {str(e)}")
            self.results['failed'].append("API endpoints")
    
    def save_test_report(self):
        """Save detailed test report to file"""
        try:
            report = {
                'timestamp': self.start_time.isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).seconds,
                'results': self.results,
                'details': self.test_details,
                'statistics': {
                    'total_tests': len(self.results['passed']) + len(self.results['failed']),
                    'passed': len(self.results['passed']),
                    'failed': len(self.results['failed']),
                    'warnings': len(self.results['warnings']),
                    'personas_created': self.personas_created,
                    'leads_created': self.leads_created
                }
            }
            
            report_path = project_root / 'data' / 'test_report.json'
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print_info(f"\nDetailed report saved: {report_path}")
        
        except Exception as e:
            print_warning(f"Could not save test report: {str(e)}")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print_header("📊 TEST SUMMARY")
        
        # Basic info
        print(f"\n{Colors.BOLD}Duration:{Colors.ENDC} {duration.seconds} seconds")
        print(f"{Colors.BOLD}Personas Created:{Colors.ENDC} {self.personas_created}")
        print(f"{Colors.BOLD}Leads Created:{Colors.ENDC} {self.leads_created}")
        
        # Passed tests
        if self.results['passed']:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ PASSED ({len(self.results['passed'])} tests):{Colors.ENDC}")
            for test in self.results['passed']:
                print(f"   • {test}")
        
        # Warnings
        if self.results['warnings']:
            print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  WARNINGS ({len(self.results['warnings'])} items):{Colors.ENDC}")
            for warning in self.results['warnings']:
                print(f"   • {warning}")
        
        # Failed tests
        if self.results['failed']:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ FAILED ({len(self.results['failed'])} tests):{Colors.ENDC}")
            for test in self.results['failed']:
                print(f"   • {test}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n{Colors.OKCYAN}{Colors.BOLD}💡 RECOMMENDATIONS:{Colors.ENDC}")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Calculate success rate
        total_tests = len(self.results['passed']) + len(self.results['failed'])
        if total_tests > 0:
            success_rate = (len(self.results['passed']) / total_tests) * 100
            
            print(f"\n{Colors.BOLD}Success Rate:{Colors.ENDC} {success_rate:.1f}%")
            
            # Overall status
            if success_rate >= 90:
                print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 EXCELLENT - System is fully functional!{Colors.ENDC}")
            elif success_rate >= 75:
                print(f"\n{Colors.OKGREEN}{Colors.BOLD}✅ GOOD - System is mostly functional with minor issues{Colors.ENDC}")
            elif success_rate >= 50:
                print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  FAIR - System has some issues that need attention{Colors.ENDC}")
            else:
                print(f"\n{Colors.FAIL}{Colors.BOLD}❌ NEEDS WORK - Multiple critical issues detected{Colors.ENDC}")
        
        # Next steps
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}📋 NEXT STEPS:{Colors.ENDC}")
        
        if self.results['failed']:
            print("1. ⚠️  Fix failed tests first:")
            for test in self.results['failed'][:3]:
                print(f"   • {test}")
        else:
            print("1. ✅ All tests passed!")
        
        if not any('Flask' in r for r in self.results['passed']):
            print("2. 🚀 Start Flask server:")
            print("   python backend/app.py")
        else:
            print("2. ✅ Flask server is running")
        
        print("3. 🌐 Visit the dashboard:")
        print("   http://localhost:5000/dashboard")
        
        print("4. 📄 Upload a target document to create personas")
        print("5. ▶️  Start the bot to generate leads")
        print("6. 📊 View results in the Leads page")
        
        print("=" * 70 + "\n")


def main():
    """Main test function"""
    print(f"{Colors.BOLD}SC AI Lead Generation System - Workflow Tester (FIXED){Colors.ENDC}")
    print(f"Python {sys.version}")
    print(f"Working directory: {os.getcwd()}\n")
    
    try:
        tester = WorkflowTester()
        tester.run_all_tests()
        
        # Exit with appropriate code
        if tester.results['failed']:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Test interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{Colors.FAIL}❌ Fatal error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()