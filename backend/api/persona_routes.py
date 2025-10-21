"""
SC AI Lead Generation System - Persona Routes  
Manual persona creation and management (NO document upload)
UPDATED: Support for all enhanced persona fields
"""

from flask import request, jsonify
from datetime import datetime
import json


def register_persona_routes(app, db_manager):
    """Register all persona management routes"""
    
    @app.route('/api/personas', methods=['GET'])
    def get_personas():
        """Get all personas"""
        try:
            personas = db_manager.get_all_personas()
            return jsonify({
                'success': True,
                'personas': personas
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/personas/create', methods=['POST'])
    def create_persona():
        """Create a new persona manually (no document upload)"""
        try:
            data = request.json
            print(f"📥 Received persona data: {data}")
            
            # Required fields
            name = data.get('name', '').strip()
            if not name:
                return jsonify({
                    'success': False,
                    'message': 'Persona name is required'
                }), 400
            
            # Check if persona already exists
            existing = db_manager.get_persona_by_name(name)
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Persona "{name}" already exists'
                }), 400
            
            # Job titles (required)
            job_titles = data.get('job_titles', '')
            if isinstance(job_titles, str):
                job_titles = job_titles.strip()
            if not job_titles:
                return jsonify({
                    'success': False,
                    'message': 'At least one job title is required'
                }), 400
            
            # Demographics
            age_range = data.get('age_range', '').strip()
            gender_distribution = data.get('gender_distribution', '').strip()
            
            # Job & Company
            seniority_level = data.get('seniority_level', '').strip()
            industry_focus = data.get('industry_focus', '').strip()
            company_size = data.get('company_size', '').strip()
            company_types = data.get('company_types', '').strip()
            
            # AI Scoring
            pain_points = data.get('pain_points', '').strip()
            goals = data.get('goals', '').strip()
            keywords = data.get('keywords', '').strip()
            decision_makers = data.get('decision_makers', '').strip()
            
            # Location targeting
            worldwide = data.get('worldwide', False)
            regions = data.get('regions', '')
            countries = data.get('countries', '')
            cities = data.get('cities', '')
            
            # Parse location arrays
            if isinstance(regions, str):
                regions = [r.strip() for r in regions.split('\n') if r.strip()]
            if isinstance(countries, str):
                countries = [c.strip() for c in countries.split('\n') if c.strip()]
            if isinstance(cities, str):
                cities = [c.strip() for c in cities.split('\n') if c.strip()]
            
            # Build location JSON
            location_data = {
                'worldwide': worldwide,
                'regions': regions if not worldwide else [],
                'countries': countries if not worldwide else [],
                'cities': cities if not worldwide else []
            }
            
            # Optional description
            description = data.get('description', '').strip()
            
            # Generate smart LinkedIn search query
            search_query = build_linkedin_search_query(
                job_titles=job_titles.split('\n') if isinstance(job_titles, str) else job_titles,
                location_targeting=location_data,
                seniority_level=seniority_level
            )
            
            print(f"🔍 Generated search query: {search_query}")
            
            # Create persona with ALL fields
            persona_id = db_manager.create_persona(
                name=name,
                description=description,
                age_range=age_range,
                gender_distribution=gender_distribution,
                job_titles=job_titles,
                decision_maker_roles=decision_makers,
                company_types=company_types,
                company_size=company_size,
                seniority_level=seniority_level,
                industry_focus=industry_focus,
                pain_points=pain_points,
                goals=goals,
                linkedin_keywords=keywords,
                smart_search_query=search_query,
                location_data=json.dumps(location_data)  # Store as JSON string
            )
            
            if persona_id:
                db_manager.log_activity(
                    activity_type='persona_created',
                    description=f'✅ Created persona: {name} (Manual)',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Persona "{name}" created successfully',
                    'persona_id': persona_id,
                    'search_query': search_query
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to create persona'
                }), 500
                
        except Exception as e:
            print(f"❌ Error creating persona: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/personas/<int:persona_id>', methods=['PUT'])
    def update_persona(persona_id):
        """Update an existing persona"""
        try:
            data = request.json
            
            # Get existing persona
            persona = db_manager.get_persona_by_id(persona_id)
            if not persona:
                return jsonify({
                    'success': False,
                    'message': 'Persona not found'
                }), 404
            
            # Parse fields (use existing values as defaults)
            name = data.get('name', persona['name']).strip()
            description = data.get('description', persona.get('description', '')).strip()
            
            # Demographics
            age_range = data.get('age_range', persona.get('age_range', '')).strip()
            gender_distribution = data.get('gender_distribution', persona.get('gender_distribution', '')).strip()
            
            # Job & Company
            job_titles = data.get('job_titles', persona.get('job_titles', '')).strip()
            seniority_level = data.get('seniority_level', persona.get('seniority_level', '')).strip()
            industry_focus = data.get('industry_focus', persona.get('industry_focus', '')).strip()
            company_size = data.get('company_size', persona.get('company_size', '')).strip()
            company_types = data.get('company_types', persona.get('company_types', '')).strip()
            
            # AI Scoring
            pain_points = data.get('pain_points', persona.get('pain_points', '')).strip()
            goals = data.get('goals', persona.get('goals', '')).strip()
            keywords = data.get('keywords', persona.get('linkedin_keywords', '')).strip()
            decision_makers = data.get('decision_makers', persona.get('decision_maker_roles', '')).strip()
            
            # Location targeting
            worldwide = data.get('worldwide', False)
            regions = data.get('regions', '')
            countries = data.get('countries', '')
            cities = data.get('cities', '')
            
            if isinstance(regions, str):
                regions = [r.strip() for r in regions.split('\n') if r.strip()]
            if isinstance(countries, str):
                countries = [c.strip() for c in countries.split('\n') if c.strip()]
            if isinstance(cities, str):
                cities = [c.strip() for c in cities.split('\n') if c.strip()]
            
            location_data = {
                'worldwide': worldwide,
                'regions': regions if not worldwide else [],
                'countries': countries if not worldwide else [],
                'cities': cities if not worldwide else []
            }
            
            # Generate updated search query
            search_query = build_linkedin_search_query(
                job_titles=job_titles.split('\n') if isinstance(job_titles, str) else [job_titles],
                location_targeting=location_data,
                seniority_level=seniority_level
            )
            
            # Update persona using dict format
            updates = {
                'name': name,
                'description': description,
                'age_range': age_range,
                'gender_distribution': gender_distribution,
                'job_titles': job_titles,
                'decision_maker_roles': decision_makers,
                'company_types': company_types,
                'company_size': company_size,
                'seniority_level': seniority_level,
                'industry_focus': industry_focus,
                'pain_points': pain_points,
                'goals': goals,
                'linkedin_keywords': keywords,
                'smart_search_query': search_query,
                'location_data': json.dumps(location_data)
            }
            success = db_manager.update_persona(persona_id, updates)
            
            if success:
                db_manager.log_activity(
                    activity_type='persona_updated',
                    description=f'✅ Updated persona: {name}',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Persona "{name}" updated successfully',
                    'search_query': search_query
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to update persona'
                }), 500
                
        except Exception as e:
            print(f"❌ Error updating persona: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/personas/<int:persona_id>', methods=['DELETE'])
    def delete_persona(persona_id):
        """Delete a persona"""
        try:
            persona = db_manager.get_persona_by_id(persona_id)
            if not persona:
                return jsonify({
                    'success': False,
                    'message': 'Persona not found'
                }), 404
            
            success = db_manager.delete_persona(persona_id)
            
            if success:
                db_manager.log_activity(
                    activity_type='persona_deleted',
                    description=f'🗑️ Deleted persona: {persona["name"]}',
                    status='success'
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Persona "{persona["name"]}" deleted successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to delete persona'
                }), 500
                
        except Exception as e:
            print(f"❌ Error deleting persona: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    print("✅ Persona routes registered (Manual Creation)")


def build_linkedin_search_query(job_titles, location_targeting, seniority_level=''):
    """Build optimized LinkedIn search query from targeting criteria"""
    
    query_parts = []
    
    # Job titles (most important)
    if job_titles:
        if isinstance(job_titles, str):
            job_titles = [t.strip() for t in job_titles.split('\n') if t.strip()]
        titles_str = ' OR '.join([f'"{title}"' for title in job_titles[:5]])  # Limit to 5 titles
        query_parts.append(f"({titles_str})")
    
    # Seniority level
    if seniority_level:
        query_parts.append(f'"{seniority_level}"')
    
    # Location (if not worldwide)
    if not location_targeting.get('worldwide', False):
        locations = []
        
        # Cities (most specific)
        if location_targeting.get('cities'):
            locations.extend(location_targeting['cities'][:3])  # Limit to 3 cities
        
        # Countries (if no cities)
        elif location_targeting.get('countries'):
            locations.extend(location_targeting['countries'][:3])  # Limit to 3 countries
        
        # Regions (if no countries)
        elif location_targeting.get('regions'):
            locations.extend(location_targeting['regions'][:2])  # Limit to 2 regions
        
        if locations:
            loc_str = ' OR '.join([f'"{loc}"' for loc in locations])
            query_parts.append(f"({loc_str})")
    
    # Combine all parts
    search_query = ' '.join(query_parts)
    
    # Limit query length (LinkedIn has search limits)
    if len(search_query) > 300:
        search_query = search_query[:300] + '...'
    
    return search_query