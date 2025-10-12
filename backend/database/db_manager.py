"""
SC AI Lead Generation System - Database Manager (FIXED)
CRUD operations for all database models
"""

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config
from backend.database.models import Base, User, Persona, Lead, Message, Campaign, Response, ActivityLog


class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, database_url=None):
        """Initialize database connection"""
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=Config.DEBUG)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        print("✅ All database tables created successfully!")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        print("⚠️  All database tables dropped!")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ==========================================
    # USER OPERATIONS
    # ==========================================
    
    def create_user(self, email, linkedin_email=None, linkedin_password=None, openai_api_key=None):
        """Create a new user"""
        with self.session_scope() as session:
            user = User(
                email=email,
                linkedin_email=linkedin_email,
                linkedin_password=linkedin_password,
                openai_api_key=openai_api_key
            )
            session.add(user)
            session.flush()
            return user.id
    
    def get_user_by_email(self, email):
        """Get user by email"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.email == email).first()
            
            if not user:
                return None
            
            # Serialize user data while session is open
            user_data = {
                'id': user.id,
                'email': user.email,
                'linkedin_email': user.linkedin_email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            return user_data
    
    def update_user_credentials(self, user_id, linkedin_email=None, linkedin_password=None, openai_api_key=None):
        """Update user credentials"""
        with self.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                if linkedin_email:
                    user.linkedin_email = linkedin_email
                if linkedin_password:
                    user.linkedin_password = linkedin_password
                if openai_api_key:
                    user.openai_api_key = openai_api_key
                user.updated_at = datetime.utcnow()
                return True
            return False
    
    # ==========================================
    # PERSONA OPERATIONS
    # ==========================================
    
    def create_persona(self, name, description=None, age_range=None, gender_distribution=None,
                      goals=None, pain_points=None, key_message=None, message_tone=None):
        """Create a new persona"""
        with self.session_scope() as session:
            persona = Persona(
                name=name,
                description=description,
                age_range=age_range,
                gender_distribution=gender_distribution,
                goals=goals,
                pain_points=pain_points,
                key_message=key_message,
                message_tone=message_tone
            )
            session.add(persona)
            session.flush()
            return persona.id
    
    def get_all_personas(self):
        """Get all personas - returns serialized dictionaries"""
        with self.session_scope() as session:
            personas = session.query(Persona).all()
            
            # Serialize personas while session is still open
            personas_data = []
            for p in personas:
                personas_data.append({
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'age_range': p.age_range,
                    'gender_distribution': p.gender_distribution,
                    'goals': p.goals,
                    'pain_points': p.pain_points,
                    'key_message': p.key_message,
                    'message_tone': p.message_tone,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                    'updated_at': p.updated_at.isoformat() if p.updated_at else None
                })
            
            return personas_data
    
    def get_persona_by_name(self, name):
        """Get persona by name"""
        with self.session_scope() as session:
            return session.query(Persona).filter(Persona.name == name).first()
    
    # ==========================================
    # LEAD OPERATIONS
    # ==========================================
    
    def create_lead(self, name, profile_url, title=None, company=None, industry=None,
                   location=None, headline=None, summary=None, company_size=None):
        """Create a new lead"""
        with self.session_scope() as session:
            # Check if lead already exists
            existing = session.query(Lead).filter(Lead.profile_url == profile_url).first()
            if existing:
                return existing.id
            
            lead = Lead(
                name=name,
                profile_url=profile_url,
                title=title,
                company=company,
                industry=industry,
                location=location,
                headline=headline,
                summary=summary,
                company_size=company_size
            )
            session.add(lead)
            session.flush()
            return lead.id
    
    def get_lead_by_id(self, lead_id):
        """Get lead by ID"""
        with self.session_scope() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            
            if not lead:
                return None
            
            # Serialize lead while session is open
            lead_data = {
                'id': lead.id,
                'name': lead.name,
                'title': lead.title,
                'company': lead.company,
                'industry': lead.industry,
                'location': lead.location,
                'profile_url': lead.profile_url,
                'headline': lead.headline,
                'summary': lead.summary,
                'company_size': lead.company_size,
                'ai_score': lead.ai_score,
                'status': lead.status,
                'connection_status': lead.connection_status,
                'persona_id': lead.persona_id,
                'persona_name': lead.persona.name if lead.persona else None,
                'score_reasoning': lead.score_reasoning,
                'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else None,
                'contacted_at': lead.contacted_at.isoformat() if lead.contacted_at else None,
                'replied_at': lead.replied_at.isoformat() if lead.replied_at else None
            }
            
            return lead_data
    
    def get_all_leads(self, status=None, min_score=None, persona_id=None, limit=None):
        """Get all leads with optional filters"""
        with self.session_scope() as session:
            query = session.query(Lead)
            
            if status:
                query = query.filter(Lead.status == status)
            if min_score:
                query = query.filter(Lead.ai_score >= min_score)
            if persona_id:
                query = query.filter(Lead.persona_id == persona_id)
            
            query = query.order_by(desc(Lead.ai_score))
            
            if limit:
                query = query.limit(limit)
            
            leads = query.all()
            
            # Serialize leads while session is open
            leads_data = []
            for lead in leads:
                leads_data.append({
                    'id': lead.id,
                    'name': lead.name,
                    'title': lead.title,
                    'company': lead.company,
                    'industry': lead.industry,
                    'location': lead.location,
                    'profile_url': lead.profile_url,
                    'headline': lead.headline,
                    'ai_score': lead.ai_score,
                    'status': lead.status,
                    'connection_status': lead.connection_status,
                    'persona_id': lead.persona_id,
                    'persona_name': lead.persona.name if lead.persona else None,
                    'scraped_at': lead.scraped_at.isoformat() if lead.scraped_at else None
                })
            
            return leads_data
        
    def update_lead_score(self, lead_id, ai_score, persona_id=None, score_reasoning=None):
        """Update lead AI score"""
        with self.session_scope() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.ai_score = ai_score
                if persona_id:
                    lead.persona_id = persona_id
                if score_reasoning:
                    lead.score_reasoning = score_reasoning
                lead.updated_at = datetime.utcnow()
                return True
            return False
    
    def update_lead_status(self, lead_id, status, connection_status=None):
        """Update lead status"""
        with self.session_scope() as session:
            lead = session.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.status = status
                if connection_status:
                    lead.connection_status = connection_status
                
                if status == 'contacted' and not lead.contacted_at:
                    lead.contacted_at = datetime.utcnow()
                elif status == 'replied' and not lead.replied_at:
                    lead.replied_at = datetime.utcnow()
                
                lead.updated_at = datetime.utcnow()
                return True
            return False
    
    # ==========================================
    # MESSAGE OPERATIONS
    # ==========================================
    
    def create_message(self, lead_id, message_type, content, campaign_id=None, 
                      variant=None, prompt_used=None, generated_by='gpt-4'):
        """Create a new message"""
        with self.session_scope() as session:
            message = Message(
                lead_id=lead_id,
                campaign_id=campaign_id,
                message_type=message_type,
                content=content,
                variant=variant,
                prompt_used=prompt_used,
                generated_by=generated_by
            )
            session.add(message)
            session.flush()
            return message.id
    
    def get_messages_by_lead(self, lead_id):
        """Get all messages for a lead"""
        with self.session_scope() as session:
            return session.query(Message).filter(Message.lead_id == lead_id).all()
    
    def update_message_status(self, message_id, status, sent_at=None):
        """Update message status"""
        with self.session_scope() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                message.status = status
                if sent_at:
                    message.sent_at = sent_at
                elif status == 'sent':
                    message.sent_at = datetime.utcnow()
                message.updated_at = datetime.utcnow()
                return True
            return False
    
    # ==========================================
    # CAMPAIGN OPERATIONS
    # ==========================================
    
    def create_campaign(self, user_id, name, description=None, search_filters=None):
        """Create a new campaign"""
        with self.session_scope() as session:
            campaign = Campaign(
                user_id=user_id,
                name=name,
                description=description,
                search_filters=search_filters
            )
            session.add(campaign)
            session.flush()
            return campaign.id
    
    def get_campaign_by_id(self, campaign_id):
        """Get campaign by ID"""
        with self.session_scope() as session:
            return session.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    def update_campaign_metrics(self, campaign_id, **metrics):
        """Update campaign metrics"""
        with self.session_scope() as session:
            campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
            if campaign:
                for key, value in metrics.items():
                    if hasattr(campaign, key):
                        setattr(campaign, key, value)
                campaign.updated_at = datetime.utcnow()
                return True
            return False
    
    # ==========================================
    # RESPONSE OPERATIONS
    # ==========================================
    
    def create_response(self, lead_id, response_text, response_type, sentiment=None,
                       intent=None, next_action=None):
        """Create a new response"""
        with self.session_scope() as session:
            response = Response(
                lead_id=lead_id,
                response_text=response_text,
                response_type=response_type,
                sentiment=sentiment,
                intent=intent,
                next_action=next_action
            )
            session.add(response)
            session.flush()
            return response.id
    
    # ==========================================
    # ACTIVITY LOG OPERATIONS
    # ==========================================
    
    def log_activity(self, activity_type, description, status='success', 
                    lead_id=None, campaign_id=None, error_message=None):
        """Log an activity"""
        with self.session_scope() as session:
            log = ActivityLog(
                activity_type=activity_type,
                description=description,
                status=status,
                lead_id=lead_id,
                campaign_id=campaign_id,
                error_message=error_message
            )
            session.add(log)
            session.flush()
            return log.id
    
    def get_recent_activities(self, limit=50):
        """Get recent activity logs - returns serialized dictionaries"""
        with self.session_scope() as session:
            logs = session.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit).all()
            
            # Serialize logs while session is still open
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log.id,
                    'activity_type': log.activity_type,
                    'description': log.description,
                    'status': log.status,
                    'error_message': log.error_message,
                    'lead_id': log.lead_id,
                    'campaign_id': log.campaign_id,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                })
            
            return logs_data
    
    # ==========================================
    # ANALYTICS OPERATIONS
    # ==========================================
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        with self.session_scope() as session:
            stats = {
                'total_leads': session.query(Lead).count(),
                'qualified_leads': session.query(Lead).filter(Lead.ai_score >= 70).count(),
                'messages_sent': session.query(Message).filter(Message.status == 'sent').count(),
                'replies_received': session.query(Response).count(),
                'avg_score': session.query(func.avg(Lead.ai_score)).scalar() or 0,
            }
            return stats
    
    def get_leads_by_persona(self):
        """Get lead count by persona"""
        with self.session_scope() as session:
            results = session.query(
                Persona.name,
                func.count(Lead.id).label('count')
            ).join(Lead).group_by(Persona.name).all()
            
            return {name: count for name, count in results}
    
    def get_message_performance(self):
        """Get message performance metrics"""
        with self.session_scope() as session:
            total_sent = session.query(Message).filter(Message.status == 'sent').count()
            total_replied = session.query(Message).filter(Message.was_replied == True).count()
            
            reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'total_sent': total_sent,
                'total_replied': total_replied,
                'reply_rate': round(reply_rate, 2)
            }


# Singleton instance
db_manager = DatabaseManager()