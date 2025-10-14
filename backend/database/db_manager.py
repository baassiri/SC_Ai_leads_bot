"""
SC AI Lead Generation System - Database Manager
CRUD operations for all database models
FIXED VERSION - AB test methods properly indented inside class
"""

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from datetime import datetime, timedelta
import sys
from pathlib import Path

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
    
    # USER OPERATIONS
    
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
    
    # PERSONA OPERATIONS
    
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
        """Get all personas"""
        with self.session_scope() as session:
            personas = session.query(Persona).all()
            
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
    
    def get_persona_by_id(self, persona_id):
        """Get a single persona by ID"""
        try:
            with self.session_scope() as session:
                persona = session.query(Persona).filter(Persona.id == persona_id).first()
                
                if not persona:
                    return None
                
                return {
                    'id': persona.id,
                    'name': persona.name,
                    'description': persona.description,
                    'goals': persona.goals,
                    'pain_points': persona.pain_points,
                    'message_tone': persona.message_tone
                }
        except Exception as e:
            print(f"Error getting persona: {str(e)}")
            return None
    
    # LEAD OPERATIONS
    
    def create_lead(self, name, profile_url, title=None, company=None, industry=None,
                   location=None, headline=None, summary=None, company_size=None):
        """Create a new lead"""
        with self.session_scope() as session:
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
        try:
            with self.session_scope() as session:
                lead = session.query(Lead).filter(Lead.id == lead_id).first()
                
                if not lead:
                    return None
                
                return {
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
        except Exception as e:
            print(f"Error getting lead: {str(e)}")
            return None
    
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
    
    # MESSAGE OPERATIONS
    
    def create_message(self, lead_id, message_type, content, campaign_id=None, 
                      variant=None, prompt_used=None, generated_by='gpt-4', status='draft'):
        """Create a new message"""
        try:
            with self.session_scope() as session:
                message = Message(
                    lead_id=lead_id,
                    campaign_id=campaign_id,
                    message_type=message_type,
                    content=content,
                    variant=variant,
                    prompt_used=prompt_used,
                    generated_by=generated_by,
                    status=status
                )
                session.add(message)
                session.flush()
                return message.id
        except Exception as e:
            print(f"Error creating message: {str(e)}")
            return None
    
    def get_pending_messages(self, limit=50):
        """Get messages that are approved and ready to send"""
        with self.session_scope() as session:
            messages = session.query(Message).join(Lead).filter(
                Message.status == 'approved',
                Message.sent_at == None
            ).order_by(Message.created_at).limit(limit).all()
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'lead_id': msg.lead_id,
                    'lead_name': msg.lead.name if msg.lead else None,
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'variant': msg.variant,
                    'status': msg.status,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                })
            
            return messages_data
    
    def get_approved_messages_count(self):
        """Get count of approved messages waiting to be sent"""
        with self.session_scope() as session:
            count = session.query(Message).filter(
                Message.status == 'approved',
                Message.sent_at == None
            ).count()
            return count
    
    def get_messages_by_status(self, status, limit=100):
        """Get messages by status"""
        with self.session_scope() as session:
            messages = session.query(Message).filter(
                Message.status == status
            ).order_by(desc(Message.created_at)).limit(limit).all()
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'lead_id': msg.lead_id,
                    'lead_name': msg.lead.name if msg.lead else None,
                    'message_type': msg.message_type,
                    'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                    'variant': msg.variant,
                    'status': msg.status,
                    'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                })
            
            return messages_data
    
    def get_messages_by_status_with_lead_info(self, status=None, lead_id=None, limit=100):
        """Get messages by status with lead information included"""
        with self.session_scope() as session:
            query = session.query(Message).join(Lead)
            
            if status:
                query = query.filter(Message.status == status)
            
            if lead_id:
                query = query.filter(Message.lead_id == lead_id)
            
            messages = query.order_by(desc(Message.created_at)).limit(limit).all()
            
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'id': msg.id,
                    'lead_id': msg.lead_id,
                    'lead_name': msg.lead.name if msg.lead else 'Unknown',
                    'lead_title': msg.lead.title if msg.lead else None,
                    'lead_company': msg.lead.company if msg.lead else None,
                    'message_type': msg.message_type,
                    'content': msg.content,
                    'variant': msg.variant,
                    'status': msg.status,
                    'generated_by': msg.generated_by,
                    'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                    'updated_at': msg.updated_at.isoformat() if msg.updated_at else None
                })
            return messages_data
    
    def get_message_stats(self):
        """Get message statistics"""
        with self.session_scope() as session:
            stats = {
                'draft': session.query(Message).filter(Message.status == 'draft').count(),
                'approved': session.query(Message).filter(Message.status == 'approved').count(),
                'sent': session.query(Message).filter(Message.status == 'sent').count(),
                'total': session.query(Message).count()
            }
            return stats
    
    def delete_message(self, message_id):
        """Delete a message"""
        with self.session_scope() as session:
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                session.delete(message)
                return True
            return False

    def get_messages_by_lead(self, lead_id):
        """Get all messages for a lead"""
        try:
            with self.session_scope() as session:
                messages = session.query(Message).filter(
                    Message.lead_id == lead_id
                ).order_by(Message.created_at.desc()).all()
                
                return messages
        except Exception as e:
            print(f"Error getting messages: {str(e)}")
            return []
    
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
    
    # CAMPAIGN OPERATIONS
    
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
    
    # RESPONSE OPERATIONS
    
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
    
    # ACTIVITY LOG OPERATIONS
    
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
        """Get recent activity logs"""
        with self.session_scope() as session:
            logs = session.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(limit).all()
            
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
    
    # ANALYTICS OPERATIONS
    
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
    
    # =============================================================================
    # AB TEST OPERATIONS
    # =============================================================================
    
    def create_ab_test(self, test_name, campaign_id=None, lead_persona=None, min_sends=20):
        """Create a new A/B/C test"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            ab_test = ABTest(
                test_name=test_name,
                campaign_id=campaign_id,
                lead_persona=lead_persona,
                min_sends_required=min_sends
            )
            session.add(ab_test)
            session.flush()
            
            print(f"✅ Created A/B test: {test_name} (ID: {ab_test.id})")
            return ab_test.id

    def get_ab_test_by_id(self, test_id):
        """Get AB test by ID with all statistics"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            test = session.query(ABTest).filter(ABTest.id == test_id).first()
            
            if not test:
                return None
            
            return {
                'id': test.id,
                'test_name': test.test_name,
                'campaign_id': test.campaign_id,
                'lead_persona': test.lead_persona,
                'status': test.status,
                'winning_variant': test.winning_variant,
                'variant_a': test.get_variant_stats('A'),
                'variant_b': test.get_variant_stats('B'),
                'variant_c': test.get_variant_stats('C'),
                'min_sends_required': test.min_sends_required,
                'confidence_threshold': test.confidence_threshold,
                'created_at': test.created_at.isoformat() if test.created_at else None,
                'completed_at': test.completed_at.isoformat() if test.completed_at else None
            }

    def get_all_ab_tests(self, status=None):
        """Get all AB tests, optionally filtered by status"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            query = session.query(ABTest)
            
            if status:
                query = query.filter(ABTest.status == status)
            
            tests = query.order_by(desc(ABTest.created_at)).all()
            
            tests_data = []
            for test in tests:
                total_sent = test.variant_a_sent + test.variant_b_sent + test.variant_c_sent
                total_replies = test.variant_a_replies + test.variant_b_replies + test.variant_c_replies
                
                tests_data.append({
                    'id': test.id,
                    'test_name': test.test_name,
                    'status': test.status,
                    'winning_variant': test.winning_variant,
                    'total_sent': total_sent,
                    'total_replies': total_replies,
                    'overall_reply_rate': (total_replies / total_sent * 100) if total_sent > 0 else 0,
                    'created_at': test.created_at.isoformat() if test.created_at else None
                })
            
            return tests_data

    def get_active_ab_tests(self):
        """Get all active AB tests"""
        return self.get_all_ab_tests(status='active')

    def get_next_variant_for_test(self, test_id):
        """Get the next variant to assign using round-robin"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            test = session.query(ABTest).filter(ABTest.id == test_id).first()
            
            if not test:
                return 'A'
            
            sends = {
                'A': test.variant_a_sent,
                'B': test.variant_b_sent,
                'C': test.variant_c_sent
            }
            
            return min(sends, key=sends.get)

    def record_ab_test_message_sent(self, test_id, variant):
        """Record that a message was sent for a specific variant"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            test = session.query(ABTest).filter(ABTest.id == test_id).first()
            
            if not test:
                return False
            
            variant = variant.upper()
            variant_lower = variant.lower()
            
            current_sent = getattr(test, f'variant_{variant_lower}_sent')
            setattr(test, f'variant_{variant_lower}_sent', current_sent + 1)
            
            print(f"📧 Recorded send for Variant {variant} in test '{test.test_name}'")
            return True

    def record_ab_test_reply(self, test_id, variant, sentiment_score=0.5):
        """Record a reply for a variant and recalculate metrics"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            import statistics
            
            test = session.query(ABTest).filter(ABTest.id == test_id).first()
            
            if not test:
                return False
            
            variant = variant.upper()
            variant_lower = variant.lower()
            
            replies = getattr(test, f'variant_{variant_lower}_replies')
            positive_replies = getattr(test, f'variant_{variant_lower}_positive_replies')
            avg_sentiment = getattr(test, f'variant_{variant_lower}_avg_sentiment')
            sent = getattr(test, f'variant_{variant_lower}_sent')
            
            new_replies = replies + 1
            new_positive = positive_replies + (1 if sentiment_score > 0.6 else 0)
            new_avg_sentiment = ((avg_sentiment * replies) + sentiment_score) / new_replies
            new_reply_rate = (new_replies / sent * 100) if sent > 0 else 0
            
            setattr(test, f'variant_{variant_lower}_replies', new_replies)
            setattr(test, f'variant_{variant_lower}_positive_replies', new_positive)
            setattr(test, f'variant_{variant_lower}_avg_sentiment', new_avg_sentiment)
            setattr(test, f'variant_{variant_lower}_reply_rate', new_reply_rate)
            
            print(f"💬 Recorded reply for Variant {variant}: {new_reply_rate:.1f}% reply rate")
            
            self._check_and_declare_winner(test)
            
            return True

    def _check_and_declare_winner(self, test):
        """Internal method to check if test has enough data to declare winner"""
        import statistics
        
        if test.status == 'completed':
            return None
        
        if (test.variant_a_sent < test.min_sends_required or 
            test.variant_b_sent < test.min_sends_required or 
            test.variant_c_sent < test.min_sends_required):
            return None
        
        rates = {
            'A': test.variant_a_reply_rate,
            'B': test.variant_b_reply_rate,
            'C': test.variant_c_reply_rate
        }
        
        winner = max(rates, key=rates.get)
        winner_rate = rates[winner]
        
        other_rates = [r for v, r in rates.items() if v != winner]
        avg_other_rate = statistics.mean(other_rates) if other_rates else 0
        
        if winner_rate >= avg_other_rate + (test.confidence_threshold * 100):
            test.winning_variant = winner
            test.status = 'completed'
            test.completed_at = datetime.utcnow()
            
            print(f"🏆 WINNER DECLARED: Variant {winner} ({winner_rate:.1f}% reply rate)")
            print(f"   Test '{test.test_name}' completed!")
            
            return winner
        
        return None

    def update_ab_test_status(self, test_id, status):
        """Update AB test status"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            test = session.query(ABTest).filter(ABTest.id == test_id).first()
            
            if test:
                test.status = status
                if status == 'completed' and not test.completed_at:
                    test.completed_at = datetime.utcnow()
                return True
            
            return False

    def get_ab_test_leaderboard(self):
        """Get performance leaderboard of all completed tests"""
        with self.session_scope() as session:
            from backend.database.models import ABTest
            
            tests = session.query(ABTest).filter(
                ABTest.status == 'completed'
            ).order_by(desc(ABTest.completed_at)).all()
            
            leaderboard = []
            for test in tests:
                winner_stats = test.get_variant_stats(test.winning_variant) if test.winning_variant else None
                
                leaderboard.append({
                    'test_name': test.test_name,
                    'winning_variant': test.winning_variant,
                    'winner_reply_rate': winner_stats['reply_rate'] if winner_stats else 0,
                    'total_sent': (test.variant_a_sent + test.variant_b_sent + test.variant_c_sent),
                    'completed_at': test.completed_at.isoformat() if test.completed_at else None
                })
            
            return leaderboard

    def create_message_with_ab_test(self, lead_id, test_id, message_type, content, 
                                    campaign_id=None, prompt_used=None, status='draft'):
        """Create a message and automatically assign variant from AB test"""
        variant = self.get_next_variant_for_test(test_id)
        
        message_id = self.create_message(
            lead_id=lead_id,
            message_type=message_type,
            content=content,
            campaign_id=campaign_id,
            variant=variant,
            prompt_used=prompt_used,
            status=status
        )
        
        with self.session_scope() as session:
            from backend.database.models import Message
            
            message = session.query(Message).filter(Message.id == message_id).first()
            if message:
                message.ab_test_id = test_id
        
        print(f"✅ Created message with Variant {variant} for test ID {test_id}")
        
        return message_id, variant

    def get_ab_test_performance_comparison(self, test_id):
        """Get detailed performance comparison for all variants"""
        test_data = self.get_ab_test_by_id(test_id)
        
        if not test_data:
            return None
        
        variants = ['A', 'B', 'C']
        comparison = {
            'test_name': test_data['test_name'],
            'status': test_data['status'],
            'winning_variant': test_data['winning_variant'],
            'variants': []
        }
        
        for variant in variants:
            stats = test_data[f'variant_{variant.lower()}']
            comparison['variants'].append({
                'variant': variant,
                'sent': stats['sent'],
                'replies': stats['replies'],
                'reply_rate': stats['reply_rate'],
                'avg_sentiment': stats['avg_sentiment'],
                'is_winner': variant == test_data['winning_variant']
            })
        
        return comparison
    
    def get_message_by_id(self, message_id: int):
            """Get a single message by ID with lead information"""
            with self.session_scope() as session:
                message = session.query(Message).filter(Message.id == message_id).first()
                
                if not message:
                    return None
                
                return {
                    'id': message.id,
                    'lead_id': message.lead_id,
                    'lead_name': message.lead.name if message.lead else None,
                    'message_type': message.message_type,
                    'content': message.content,
                    'variant': message.variant,
                    'status': message.status,
                    'sent_at': message.sent_at.isoformat() if message.sent_at else None,
                    'created_at': message.created_at.isoformat() if message.created_at else None
                }
    def delete_lead(self, lead_id):
            """
            Delete a lead from database
            
            Args:
                lead_id: ID of lead to delete
                
            Returns:
                bool: True if deleted, False if not found
            """
            try:
                with self.get_session() as session:
                    from backend.database.models import Lead
                    lead = session.query(Lead).filter_by(id=lead_id).first()
                    if lead:
                        session.delete(lead)
                        session.commit()
                        return True
                    return False
            except Exception as e:
                print(f"Error deleting lead: {e}")
                return False

# Singleton instance
db_manager = DatabaseManager()
