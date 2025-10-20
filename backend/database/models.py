"""
SC AI Lead Generation System - Database Models
SQLAlchemy ORM models for all database tables
UPDATED: Added ABTest model for A/B/C testing integration
FIXED: Added enhanced persona fields for AI-powered targeting
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Store user credentials and settings"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    
    # LinkedIn credentials (encrypted in production)
    linkedin_email = Column(String(255))
    linkedin_password = Column(String(255))  # TODO: Encrypt this
    
    # OpenAI API
    openai_api_key = Column(String(255))  # TODO: Encrypt this
    
    # Settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Persona(Base):
    """Store target persona profiles with enhanced AI-powered targeting"""
    __tablename__ = 'personas'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # e.g., "Plastic Surgeon"
    description = Column(Text)  # e.g., "The Prestige Provider"
    
    # Demographics
    age_range = Column(String(50))  # e.g., "40-65"
    gender_distribution = Column(String(100))  # e.g., "Predominantly male"
    
    # Business details
    goals = Column(Text)  # JSON or text list of goals
    pain_points = Column(Text)  # JSON or text list of pain points
    
    # Messaging
    key_message = Column(Text)
    message_tone = Column(String(100))  # e.g., "Consultative", "Growth-focused"
    
    # ✅ ENHANCED TARGETING FIELDS (AI-generated)
    job_titles = Column(Text)  # Newline-separated job titles
    decision_maker_roles = Column(Text)  # Key decision maker roles
    company_types = Column(Text)  # Types of companies to target
    solutions = Column(Text)  # Solutions this persona needs
    linkedin_keywords = Column(Text)  # Keywords for LinkedIn search
    smart_search_query = Column(String(500))  # AI-optimized search query
    message_hooks = Column(Text)  # Proven message hooks
    seniority_level = Column(String(100))  # e.g., "C-Level", "Director"
    industry_focus = Column(String(200))  # Primary industries
    document_source = Column(String(255))  # Source document filename
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leads = relationship("Lead", back_populates="persona")
    
    def __repr__(self):
        return f"<Persona(id={self.id}, name='{self.name}')>"


class Lead(Base):
    """Store scraped LinkedIn leads"""
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    company = Column(String(255))
    industry = Column(String(255))
    location = Column(String(255))
    
    # LinkedIn details
    profile_url = Column(String(500), unique=True)
    headline = Column(Text)
    summary = Column(Text)
    company_size = Column(String(50))  # e.g., "11-50 employees"
    
    # AI Scoring
    ai_score = Column(Float, default=0.0)  # 0-100 scale
    persona_id = Column(Integer, ForeignKey('personas.id'))
    score_reasoning = Column(Text)  # Why this score?
    
    # Status tracking
    status = Column(String(50), default='new')  # new, contacted, replied, archived
    connection_status = Column(String(50), default='not_sent')  # not_sent, pending, accepted, rejected
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow)
    contacted_at = Column(DateTime)
    replied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    persona = relationship("Persona", back_populates="leads")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    responses = relationship("Response", back_populates="lead", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', score={self.ai_score})>"


class Message(Base):
    """Store AI-generated messages"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    ab_test_id = Column(Integer, ForeignKey('ab_tests.id'))
    
    # Message details
    message_type = Column(String(50))  # connection_request, follow_up_1, follow_up_2
    content = Column(Text, nullable=False)
    variant = Column(String(10))  # A, B, C (for A/B testing)
    
    # AI generation context
    prompt_used = Column(Text)  # Store the prompt for learning
    generated_by = Column(String(50), default='gpt-4')  # Model used
    
    # Status
    status = Column(String(50), default='draft')  # draft, approved, sent, failed
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    
    # Performance metrics
    was_replied = Column(Boolean, default=False)
    reply_sentiment = Column(String(50))  # positive, neutral, negative
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    ab_test = relationship("ABTest", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, type='{self.message_type}', status='{self.status}')>"


class Campaign(Base):
    """Track outreach campaigns"""
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Campaign details
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='draft')  # draft, active, paused, completed
    
    # Search criteria (stored as JSON)
    search_filters = Column(JSON)  # job titles, industries, locations, etc.
    
    # Metrics
    leads_scraped = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    connections_accepted = Column(Integer, default=0)
    replies_received = Column(Integer, default=0)
    meetings_booked = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    messages = relationship("Message", back_populates="campaign")
    ab_tests = relationship("ABTest", back_populates="campaign")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"


class ABTest(Base):
    """Track A/B/C message variant testing"""
    __tablename__ = 'ab_tests'
    
    id = Column(Integer, primary_key=True)
    test_name = Column(String(100), nullable=False)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    lead_persona = Column(String(200))
    
    # Variant A Metrics
    variant_a_sent = Column(Integer, default=0)
    variant_a_replies = Column(Integer, default=0)
    variant_a_positive_replies = Column(Integer, default=0)
    variant_a_avg_sentiment = Column(Float, default=0.0)
    variant_a_reply_rate = Column(Float, default=0.0)
    
    # Variant B Metrics
    variant_b_sent = Column(Integer, default=0)
    variant_b_replies = Column(Integer, default=0)
    variant_b_positive_replies = Column(Integer, default=0)
    variant_b_avg_sentiment = Column(Float, default=0.0)
    variant_b_reply_rate = Column(Float, default=0.0)
    
    # Variant C Metrics
    variant_c_sent = Column(Integer, default=0)
    variant_c_replies = Column(Integer, default=0)
    variant_c_positive_replies = Column(Integer, default=0)
    variant_c_avg_sentiment = Column(Float, default=0.0)
    variant_c_reply_rate = Column(Float, default=0.0)
    
    # Test Status
    winning_variant = Column(String(1))
    status = Column(String(20), default='active')  # active, completed, paused
    min_sends_required = Column(Integer, default=20)
    confidence_threshold = Column(Float, default=0.15)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="ab_tests")
    messages = relationship("Message", back_populates="ab_test")
    
    def __repr__(self):
        return f"<ABTest(id={self.id}, name='{self.test_name}', status='{self.status}')>"
    
    def get_winner(self):
        """Get the winning variant if test is completed"""
        if self.status == 'completed' and self.winning_variant:
            return self.winning_variant
        return None
    
    def get_variant_stats(self, variant: str):
        """Get statistics for a specific variant"""
        variant = variant.upper()
        if variant not in ['A', 'B', 'C']:
            return None
        
        variant_lower = variant.lower()
        return {
            'variant': variant,
            'sent': getattr(self, f'variant_{variant_lower}_sent'),
            'replies': getattr(self, f'variant_{variant_lower}_replies'),
            'positive_replies': getattr(self, f'variant_{variant_lower}_positive_replies'),
            'avg_sentiment': getattr(self, f'variant_{variant_lower}_avg_sentiment'),
            'reply_rate': getattr(self, f'variant_{variant_lower}_reply_rate')
        }


class Response(Base):
    """Store lead responses for analysis"""
    __tablename__ = 'responses'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=False)
    
    # Response details
    response_text = Column(Text, nullable=False)
    response_type = Column(String(50))  # connection_accept, message_reply, meeting_request
    sentiment = Column(String(50))  # positive, neutral, negative, interested, not_interested
    
    # AI analysis
    intent = Column(String(100))  # What does the lead want?
    next_action = Column(String(255))  # Suggested next step
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lead = relationship("Lead", back_populates="responses")
    
    def __repr__(self):
        return f"<Response(id={self.id}, sentiment='{self.sentiment}')>"


class ActivityLog(Base):
    """Log all bot activities for debugging and analytics"""
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    
    # Activity details
    activity_type = Column(String(100))  # scrape, score, message_generate, message_send, etc.
    description = Column(Text)
    status = Column(String(50))  # success, failed, pending
    
    # Associated records
    lead_id = Column(Integer, ForeignKey('leads.id'))
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    
    # Error tracking
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, type='{self.activity_type}', status='{self.status}')>"# ============================================================================
# ADD THIS MODEL TO backend/database/models.py
# Add it after the other model classes (around line 200+)
# ============================================================================

class MessageTemplate(Base):
    """Message template for reusable message patterns"""
    __tablename__ = 'message_templates'
    
    id = Column(Integer, primary_key=True)
    template = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, template='{self.template[:50]}...')>"