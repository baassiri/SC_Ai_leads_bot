"""
SC AI Lead Generation System - CSV Handler (FIXED)
Import and export lead data to/from CSV files
"""

import csv
import os
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config


class CSVHandler:
    """Handle CSV import/export operations for leads"""
    
    def __init__(self):
        """Initialize CSV handler with export directory"""
        self.export_dir = Config.EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_leads_to_csv(self, leads, filename=None):
        """
        Export leads to CSV file
        
        Args:
            leads: List of Lead objects or dictionaries
            filename: Optional custom filename
            
        Returns:
            str: Path to exported CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'leads_export_{timestamp}.csv'
        
        filepath = self.export_dir / filename
        
        # Define CSV headers
        headers = [
            'id', 'name', 'title', 'company', 'industry', 'location',
            'profile_url', 'headline', 'company_size', 'ai_score',
            'persona', 'status', 'connection_status', 'scraped_at'
        ]
        
        # FIXED: Added extrasaction='ignore' to handle extra fields
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            
            for lead in leads:
                # Handle both ORM objects and dictionaries
                if hasattr(lead, '__dict__'):
                    # ORM object - extract fields manually
                    lead_data = {
                        'id': lead.id,
                        'name': lead.name,
                        'title': lead.title or '',
                        'company': lead.company or '',
                        'industry': lead.industry or '',
                        'location': lead.location or '',
                        'profile_url': lead.profile_url or '',
                        'headline': lead.headline or '',
                        'company_size': lead.company_size or '',
                        'ai_score': lead.ai_score or 0,
                        'persona': lead.persona.name if lead.persona else '',
                        'status': lead.status or 'new',
                        'connection_status': lead.connection_status or 'not_sent',
                        'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else ''
                    }
                else:
                    # FIXED: Dictionary - only include fields that are in headers
                    lead_data = {}
                    for key in headers:
                        if key == 'persona':
                            # Handle persona specially - might be 'persona_name' in dict
                            lead_data['persona'] = lead.get('persona_name', lead.get('persona', ''))
                        elif key in lead:
                            lead_data[key] = lead[key] if lead[key] is not None else ''
                        else:
                            lead_data[key] = ''
                
                writer.writerow(lead_data)
        
        print(f"✅ Exported {len(leads)} leads to {filepath}")
        return str(filepath)
    
    def import_leads_from_csv(self, filepath):
        """
        Import leads from CSV file
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            list: List of lead dictionaries
        """
        leads = []
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # Clean up empty strings to None
                lead_data = {
                    'name': row.get('name', '').strip(),
                    'title': row.get('title', '').strip() or None,
                    'company': row.get('company', '').strip() or None,
                    'industry': row.get('industry', '').strip() or None,
                    'location': row.get('location', '').strip() or None,
                    'profile_url': row.get('profile_url', '').strip() or None,
                    'headline': row.get('headline', '').strip() or None,
                    'company_size': row.get('company_size', '').strip() or None,
                    'ai_score': float(row.get('ai_score', 0)) if row.get('ai_score') else 0,
                    'status': row.get('status', 'new').strip(),
                    'connection_status': row.get('connection_status', 'not_sent').strip()
                }
                
                # Skip rows with no name or profile URL
                if lead_data['name'] and lead_data.get('profile_url'):
                    leads.append(lead_data)
        
        print(f"✅ Imported {len(leads)} leads from {filepath}")
        return leads
    
    def save_scrape_backup(self, leads, source='linkedin'):
        """
        Save a backup of scraped leads
        
        Args:
            leads: List of lead dictionaries
            source: Source of the leads (default: 'linkedin')
            
        Returns:
            str: Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'scrape_backup_{source}_{timestamp}.csv'
        
        return self.export_leads_to_csv(leads, filename)
    
    def merge_csv_files(self, csv_files, output_filename=None):
        """
        Merge multiple CSV files into one, removing duplicates
        
        Args:
            csv_files: List of CSV file paths
            output_filename: Optional output filename
            
        Returns:
            str: Path to merged CSV file
        """
        all_leads = []
        seen_urls = set()
        
        for csv_file in csv_files:
            try:
                leads = self.import_leads_from_csv(csv_file)
                for lead in leads:
                    # Use profile_url as unique identifier
                    if lead.get('profile_url') and lead['profile_url'] not in seen_urls:
                        all_leads.append(lead)
                        seen_urls.add(lead['profile_url'])
            except Exception as e:
                print(f"⚠️ Error reading {csv_file}: {str(e)}")
                continue
        
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'merged_leads_{timestamp}.csv'
        
        filepath = self.export_leads_to_csv(all_leads, output_filename)
        print(f"✅ Merged {len(csv_files)} files into {len(all_leads)} unique leads")
        
        return filepath
    
    def validate_csv_format(self, filepath):
        """
        Validate CSV file format
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            dict: Validation results with errors and warnings
        """
        errors = []
        warnings = []
        
        required_columns = ['name', 'profile_url']
        recommended_columns = ['title', 'company', 'location']
        
        try:
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                
                # Check required columns
                for col in required_columns:
                    if col not in headers:
                        errors.append(f"Missing required column: {col}")
                
                # Check recommended columns
                for col in recommended_columns:
                    if col not in headers:
                        warnings.append(f"Missing recommended column: {col}")
                
                # Check for data
                row_count = 0
                for row in reader:
                    row_count += 1
                    
                    # Check if required fields are empty
                    for col in required_columns:
                        if col in headers and not row.get(col, '').strip():
                            errors.append(f"Row {row_count}: Empty required field '{col}'")
                
                if row_count == 0:
                    warnings.append("CSV file is empty (no data rows)")
        
        except Exception as e:
            errors.append(f"Error reading CSV: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'row_count': row_count if 'row_count' in locals() else 0
        }
    
    def create_sample_csv(self, num_leads=5):
        """
        Create a sample CSV file for testing
        
        Args:
            num_leads: Number of sample leads to create
            
        Returns:
            str: Path to sample CSV file
        """
        sample_leads = [
            {
                'name': 'Dr. Sarah Johnson',
                'title': 'Cosmetic Surgeon',
                'company': 'Beverly Hills Aesthetics',
                'industry': 'Medical Practice',
                'location': 'Los Angeles, CA',
                'profile_url': 'https://www.linkedin.com/in/sample-profile-1/',
                'headline': 'Board-Certified Plastic Surgeon | Specializing in Facial Aesthetics',
                'company_size': '11-50 employees',
                'ai_score': 92,
                'persona': 'Plastic Surgeon',
                'status': 'new',
                'connection_status': 'not_sent'
            },
            {
                'name': 'Dr. Michael Chen',
                'title': 'Dermatologist',
                'company': 'Skin Perfect Clinic',
                'industry': 'Medical Practice',
                'location': 'New York, NY',
                'profile_url': 'https://www.linkedin.com/in/sample-profile-2/',
                'headline': 'Board-Certified Dermatologist | Laser & Injectable Specialist',
                'company_size': '11-50 employees',
                'ai_score': 87,
                'persona': 'Dermatologist',
                'status': 'new',
                'connection_status': 'not_sent'
            },
            {
                'name': 'Jessica Williams',
                'title': 'Aesthetic Nurse Practitioner',
                'company': 'Glow Med Spa',
                'industry': 'Medical Practice',
                'location': 'Miami, FL',
                'profile_url': 'https://www.linkedin.com/in/sample-profile-3/',
                'headline': 'Aesthetic NP | Expert in Injectables & Skin Rejuvenation',
                'company_size': '1-10 employees',
                'ai_score': 76,
                'persona': 'Med Spa Owner',
                'status': 'new',
                'connection_status': 'not_sent'
            },
            {
                'name': 'Amanda Rodriguez',
                'title': 'Owner & Medical Director',
                'company': 'Luminous Aesthetics',
                'industry': 'Medical Practice',
                'location': 'Houston, TX',
                'profile_url': 'https://www.linkedin.com/in/sample-profile-4/',
                'headline': 'Med Spa Owner | Building the Future of Aesthetic Medicine',
                'company_size': '1-10 employees',
                'ai_score': 94,
                'persona': 'Med Spa Owner',
                'status': 'new',
                'connection_status': 'not_sent'
            },
            {
                'name': 'Dr. Robert Kim',
                'title': 'Plastic Surgeon',
                'company': 'Windy City Plastic Surgery',
                'industry': 'Medical Practice',
                'location': 'Chicago, IL',
                'profile_url': 'https://www.linkedin.com/in/sample-profile-5/',
                'headline': 'Board-Certified Plastic Surgeon | 15+ Years Experience',
                'company_size': '11-50 employees',
                'ai_score': 68,
                'persona': 'Plastic Surgeon',
                'status': 'new',
                'connection_status': 'not_sent'
            }
        ]
        
        # Use only the requested number of leads
        sample_leads = sample_leads[:num_leads]
        
        filename = 'sample_leads.csv'
        filepath = self.export_leads_to_csv(sample_leads, filename)
        
        print(f"✅ Created sample CSV with {num_leads} leads")
        return filepath


# Singleton instance
csv_handler = CSVHandler()


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV Handler for Lead Management')
    parser.add_argument('--create-sample', type=int, help='Create sample CSV with N leads')
    parser.add_argument('--validate', type=str, help='Validate CSV file')
    parser.add_argument('--import', dest='import_file', type=str, help='Import CSV file')
    parser.add_argument('--merge', nargs='+', help='Merge multiple CSV files')
    
    args = parser.parse_args()
    
    if args.create_sample:
        filepath = csv_handler.create_sample_csv(args.create_sample)
        print(f"Sample CSV created at: {filepath}")
    
    elif args.validate:
        result = csv_handler.validate_csv_format(args.validate)
        print(f"\nValidation Results:")
        print(f"Valid: {result['valid']}")
        print(f"Rows: {result['row_count']}")
        
        if result['errors']:
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print(f"\n⚠️ Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
    
    elif args.import_file:
        leads = csv_handler.import_leads_from_csv(args.import_file)
        print(f"\nImported {len(leads)} leads:")
        for i, lead in enumerate(leads[:5], 1):
            print(f"{i}. {lead['name']} - {lead.get('title', 'N/A')} at {lead.get('company', 'N/A')}")
        
        if len(leads) > 5:
            print(f"... and {len(leads) - 5} more")
    
    elif args.merge:
        output_file = csv_handler.merge_csv_files(args.merge)
        print(f"Merged file saved to: {output_file}")
    
    else:
        parser.print_help()