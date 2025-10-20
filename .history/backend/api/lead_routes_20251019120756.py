from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import sqlite3
import csv
import io
from functools import wraps

lead_routes = Blueprint('lead_routes', __name__)

# Database helper
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Authentication decorator (adjust based on your auth system)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, we'll assume user is authenticated
        return f(*args, **kwargs)
    return decorated_function

@lead_routes.route('/api/leads', methods=['GET'])
@login_required
def get_leads():
    """Get all leads with stats"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all leads with campaign info
        cursor.execute('''
            SELECT 
                l.*,
                c.name as campaign_name
            FROM leads l
            LEFT JOIN campaigns c ON l.campaign_id = c.id
            ORDER BY l.created_at DESC
        ''')
        
        leads = [dict(row) for row in cursor.fetchall()]
        
        # Calculate stats
        stats = {
            'total': len(leads),
            'new': sum(1 for l in leads if l['status'] == 'new'),
            'contacted': sum(1 for l in leads if l['status'] == 'contacted'),
            'replied': sum(1 for l in leads if l['status'] == 'replied'),
            'interested': sum(1 for l in leads if l['status'] == 'interested'),
            'not_interested': sum(1 for l in leads if l['status'] == 'not_interested')
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'leads': leads,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/<int:lead_id>', methods=['GET'])
@login_required
def get_lead(lead_id):
    """Get single lead details"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                l.*,
                c.name as campaign_name
            FROM leads l
            LEFT JOIN campaigns c ON l.campaign_id = c.id
            WHERE l.id = ?
        ''', (lead_id,))
        
        lead = cursor.fetchone()
        conn.close()
        
        if lead:
            return jsonify({
                'success': True,
                'lead': dict(lead)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/<int:lead_id>/timeline', methods=['GET'])
@login_required
def get_lead_timeline(lead_id):
    """Get timeline/activity history for a lead"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lead exists
        cursor.execute('SELECT id, name FROM leads WHERE id = ?', (lead_id,))
        lead = cursor.fetchone()
        
        if not lead:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        # Get timeline events
        cursor.execute('''
            SELECT 
                id,
                action,
                message,
                details,
                timestamp,
                metadata
            FROM lead_timeline
            WHERE lead_id = ?
            ORDER BY timestamp DESC
        ''', (lead_id,))
        
        timeline = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'lead_id': lead_id,
            'lead_name': lead['name'],
            'timeline': timeline
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/<int:lead_id>/timeline', methods=['POST'])
@login_required
def add_timeline_event(lead_id):
    """Add a new timeline event for a lead"""
    try:
        data = request.json
        action = data.get('action')
        message = data.get('message', '')
        details = data.get('details', '')
        metadata = data.get('metadata', '')
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lead exists
        cursor.execute('SELECT id FROM leads WHERE id = ?', (lead_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        # Insert timeline event
        cursor.execute('''
            INSERT INTO lead_timeline 
            (lead_id, action, message, details, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (lead_id, action, message, details, metadata, datetime.now()))
        
        # Update lead's last_contact
        cursor.execute('''
            UPDATE leads 
            SET last_contact = ?
            WHERE id = ?
        ''', (datetime.now(), lead_id))
        
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'message': 'Timeline event added'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads', methods=['POST'])
@login_required
def create_lead():
    """Create a new lead"""
    try:
        data = request.json
        
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lead with email already exists
        cursor.execute('SELECT id FROM leads WHERE email = ?', (data['email'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Lead with this email already exists'
            }), 400
        
        # Insert new lead
        cursor.execute('''
            INSERT INTO leads 
            (name, email, company, title, linkedin_url, phone, 
             status, campaign_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['email'],
            data.get('company', ''),
            data.get('title', ''),
            data.get('linkedin_url', ''),
            data.get('phone', ''),
            data.get('status', 'new'),
            data.get('campaign_id'),
            data.get('notes', ''),
            datetime.now()
        ))
        
        lead_id = cursor.lastrowid
        
        # Add timeline event
        cursor.execute('''
            INSERT INTO lead_timeline 
            (lead_id, action, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (lead_id, 'Lead Created', f'Lead {data["name"]} was added to the system', datetime.now()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'lead_id': lead_id,
            'message': 'Lead created successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/<int:lead_id>', methods=['PUT'])
@login_required
def update_lead(lead_id):
    """Update lead information"""
    try:
        data = request.json
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lead exists
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        old_lead = cursor.fetchone()
        
        if not old_lead:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        allowed_fields = ['name', 'email', 'company', 'title', 'linkedin_url', 
                         'phone', 'status', 'campaign_id', 'notes']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f'{field} = ?')
                values.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No fields to update'
            }), 400
        
        # Add updated_at
        update_fields.append('updated_at = ?')
        values.append(datetime.now())
        values.append(lead_id)
        
        # Update lead
        query = f"UPDATE leads SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        # Add timeline event for status change
        if 'status' in data and data['status'] != old_lead['status']:
            cursor.execute('''
                INSERT INTO lead_timeline 
                (lead_id, action, message, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (
                lead_id, 
                'Status Changed', 
                f'Status changed from {old_lead["status"]} to {data["status"]}',
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Lead updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/<int:lead_id>', methods=['DELETE'])
@login_required
def delete_lead(lead_id):
    """Delete a lead"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if lead exists
        cursor.execute('SELECT id FROM leads WHERE id = ?', (lead_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Lead not found'
            }), 404
        
        # Delete timeline events
        cursor.execute('DELETE FROM lead_timeline WHERE lead_id = ?', (lead_id,))
        
        # Delete lead
        cursor.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Lead deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/bulk-update', methods=['POST'])
@login_required
def bulk_update_leads():
    """Bulk update multiple leads"""
    try:
        data = request.json
        lead_ids = data.get('lead_ids', [])
        updates = data.get('updates', {})
        
        if not lead_ids or not updates:
            return jsonify({
                'success': False,
                'error': 'lead_ids and updates are required'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Build update query
        update_fields = []
        values = []
        
        allowed_fields = ['status', 'campaign_id', 'notes']
        
        for field in allowed_fields:
            if field in updates:
                update_fields.append(f'{field} = ?')
                values.append(updates[field])
        
        if not update_fields:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Update leads
        placeholders = ','.join('?' * len(lead_ids))
        query = f"UPDATE leads SET {', '.join(update_fields)} WHERE id IN ({placeholders})"
        cursor.execute(query, values + lead_ids)
        
        # Add timeline events
        if 'status' in updates:
            for lead_id in lead_ids:
                cursor.execute('''
                    INSERT INTO lead_timeline 
                    (lead_id, action, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    lead_id,
                    'Bulk Status Update',
                    f'Status updated to {updates["status"]}',
                    datetime.now()
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(lead_ids)} leads updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/export', methods=['GET'])
@login_required
def export_leads():
    """Export leads to CSV"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                l.id, l.name, l.email, l.company, l.title,
                l.linkedin_url, l.phone, l.status,
                c.name as campaign_name,
                l.created_at, l.last_contact
            FROM leads l
            LEFT JOIN campaigns c ON l.campaign_id = c.id
            ORDER BY l.created_at DESC
        ''')
        
        leads = cursor.fetchall()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Name', 'Email', 'Company', 'Title',
            'LinkedIn URL', 'Phone', 'Status', 'Campaign',
            'Created At', 'Last Contact'
        ])
        
        # Write data
        for lead in leads:
            writer.writerow(lead)
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'leads_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/leads/import', methods=['POST'])
@login_required
def import_leads():
    """Import leads from CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'error': 'File must be a CSV'
            }), 400
        
        # Read CSV
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        conn = get_db()
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        errors = []
        
        for row in csv_reader:
            try:
                # Check required fields
                if not row.get('name') or not row.get('email'):
                    skipped += 1
                    continue
                
                # Check if email exists
                cursor.execute('SELECT id FROM leads WHERE email = ?', (row['email'],))
                if cursor.fetchone():
                    skipped += 1
                    continue
                
                # Insert lead
                cursor.execute('''
                    INSERT INTO leads 
                    (name, email, company, title, linkedin_url, phone, 
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['name'],
                    row['email'],
                    row.get('company', ''),
                    row.get('title', ''),
                    row.get('linkedin_url', ''),
                    row.get('phone', ''),
                    row.get('status', 'new'),
                    datetime.now()
                ))
                
                lead_id = cursor.lastrowid
                
                # Add timeline event
                cursor.execute('''
                    INSERT INTO lead_timeline 
                    (lead_id, action, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (lead_id, 'Lead Imported', 'Lead imported from CSV', datetime.now()))
                
                imported += 1
                
            except Exception as e:
                errors.append(f"Row {csv_reader.line_num}: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@lead_routes.route('/api/campaigns', methods=['GET'])
@login_required
def get_campaigns():
    """Get all campaigns for dropdown"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, status FROM campaigns ORDER BY name')
        campaigns = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper function to create database tables if they don't exist
def init_lead_tables():
    """Initialize database tables for leads"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create leads table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            company TEXT,
            title TEXT,
            linkedin_url TEXT,
            phone TEXT,
            status TEXT DEFAULT 'new',
            campaign_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            last_contact TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    ''')
    
    # Create lead_timeline table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lead_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            message TEXT,
            details TEXT,
            metadata TEXT,
            timestamp TIMESTAMP NOT NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_lead ON lead_timeline(lead_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_timestamp ON lead_timeline(timestamp)')
    
    conn.commit()
    conn.close()