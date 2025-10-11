# 🤖 SC AI Lead Generation System

**AI-powered LinkedIn Sales Navigator automation platform for the aesthetics industry**

Automates the entire lead generation process — from data collection to personalized outreach — using GPT-4 and intelligent scoring algorithms.

---

## 🎯 **What It Does**

This system targets **plastic surgeons, dermatologists, med spas, day spas, wellness centers, and aesthetic clinics** to help them with:

- ✅ **Automated Lead Scraping** from LinkedIn Sales Navigator
- ✅ **AI-Powered Lead Scoring** (0-100 scale based on conversion likelihood)
- ✅ **Personalized Message Generation** using GPT-4
- ✅ **Smart Outreach Automation** with rate limiting
- ✅ **HubSpot CRM Integration** for seamless follow-up
- ✅ **Continuous Learning** from response patterns

---

## 🏗️ **System Architecture**

### **6 Progressive Phases:**

1. **Foundation** - Scrape, store, display leads
2. **Data Cleaning** - Deduplicate and validate
3. **AI Qualification** - Score and prioritize leads
4. **Message Generation** - GPT-4 personalized messages
5. **Outreach Automation** - Send messages automatically
6. **Learning & Optimization** - Improve based on results

See [SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) for detailed flow diagrams.

---

## 🚀 **Quick Start**

### **Prerequisites:**
- Python 3.10+
- LinkedIn Sales Navigator account
- OpenAI API key (GPT-4 access)
- Google Chrome browser (for Selenium)

### **Installation:**

```bash
# 1. Clone the repository
cd "C:\Users\wmmb\OneDrive\Desktop"
git clone <your-repo-url> SC_Ai_leads_bot
cd SC_Ai_leads_bot

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
copy .env.example .env
# Edit .env with your credentials

# 6. Initialize database
python scripts/init_db.py

# 7. Run the application
python backend/app.py
```

Visit: `http://localhost:5000`

---

## 📋 **Configuration**

Edit the `.env` file with your credentials:

```env
# OpenAI API
OPENAI_API_KEY=sk-your-key-here

# LinkedIn
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password

# HubSpot (optional)
HUBSPOT_API_KEY=your-hubspot-key
```

---

## 🎨 **Features**

### **1. Lead Scraping**
- Connect to LinkedIn Sales Navigator
- Apply advanced filters (job title, industry, location, company size)
- Scrape up to 100 leads per session
- Auto-save to CSV backup + SQLite database

### **2. AI Lead Scoring**
Scores leads 0-100 based on:
- Job title relevance to target personas
- Company size and industry match
- Geographic priority
- Profile completeness (engagement likelihood)

### **3. Message Generation**
GPT-4 generates 3 message variants:
- **Connection Request** - Short, personalized intro
- **Follow-Up v1** - Value-based message (2-3 days after accept)
- **Follow-Up v2** - Call-to-action for meeting (5 days after v1)

Automatically adapts tone based on persona:
- **Plastic Surgeons** → Prestige-focused, consultative
- **Dermatologists** → Clinical authority, results-driven
- **Med Spas** → Growth-oriented, data-backed
- **Day Spas** → Brand-building, retention-focused
- **Wellness Centers** → Holistic, educational

### **4. Outreach Automation**
- Rate-limited sending (10-15 messages/hour)
- Auto-follow-up scheduler
- Response tracking
- CRM sync to HubSpot

### **5. Analytics Dashboard**
Track performance:
- Connection accept rate
- Message reply rate
- Meeting booking rate
- Best-performing personas
- A/B test results

---

## 📂 **Project Structure**

```
SC_Ai_leads_bot/
├── backend/
│   ├── app.py                     # Main Flask app
│   ├── database/                  # Database models & operations
│   ├── scrapers/                  # LinkedIn scraper
│   ├── ai_engine/                 # AI scoring & messaging
│   └── automation/                # Outreach automation
├── frontend/
│   ├── static/                    # CSS, JS, images
│   └── templates/                 # HTML templates
├── data/
│   ├── uploads/                   # User-uploaded files
│   ├── exports/                   # CSV exports
│   └── database.db                # SQLite database
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## 🧠 **Target Personas**

The system understands 6 primary personas:

1. **Plastic Surgeon** - "The Prestige Provider"
2. **Dermatologist** - "The Clinical Authority"
3. **Med Spa Owner** - "The Growth Seeker"
4. **Day Spa** - "The Relaxation Brand Builder"
5. **Wellness Center** - "The Holistic Healer"
6. **Aesthetic Clinic** - Generic cosmetic practice

Each persona has unique:
- Pain points
- Goals
- Messaging tone
- Value propositions

---

## 🔧 **Tech Stack**

**Backend:**
- Python 3.10+
- Flask (web framework)
- SQLAlchemy (ORM)
- Selenium (LinkedIn automation)
- OpenAI GPT-4 (AI engine)
- Pandas (data processing)

**Frontend:**
- HTML5/CSS3
- JavaScript
- Bootstrap 5
- DataTables.js
- Chart.js

**Integrations:**
- LinkedIn Sales Navigator
- OpenAI API
- HubSpot CRM

---

## 📊 **Usage Workflow**

1. **Upload** `Targets.docx` to parse persona data
2. **Login** to LinkedIn Sales Navigator
3. **Configure** search filters (job titles, industries, locations)
4. **Scrape** leads (auto-saved to CSV + database)
5. **Review** cleaned and scored leads
6. **Generate** AI-powered messages
7. **Preview & Approve** messages before sending
8. **Automate** outreach with rate limiting
9. **Track** responses and performance
10. **Optimize** based on analytics

---

## 🛡️ **Safety Features**

- **Rate Limiting**: Max 15 messages/hour to avoid LinkedIn restrictions
- **Manual Approval**: Review messages before auto-send
- **Duplicate Detection**: Never message the same lead twice
- **Error Handling**: Graceful failures with retry logic
- **Logging**: Full audit trail of all actions

---

## 📈 **Performance Targets**

| Metric | Target |
|--------|--------|
| Connection Accept Rate | 30%+ |
| Message Reply Rate | 15%+ |
| Meeting Booking Rate | 5%+ |
| Data Quality | 95%+ |
| High-Value Lead % | 30%+ |

---

## 🐛 **Troubleshooting**

### **Selenium not working?**
```bash
pip install --upgrade selenium webdriver-manager
```

### **OpenAI API error?**
- Check your API key in `.env`
- Verify you have GPT-4 access
- Check your API usage limits

### **LinkedIn login failing?**
- Verify credentials in `.env`
- LinkedIn may require 2FA (solve manually first)
- Try using a VPN if rate-limited

---

## 📚 **Documentation**

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

## 🤝 **Contributing**

This is a private project for SC Lead Generation. 

**Development Process:**
1. Create feature branch
2. Test locally
3. Submit pull request
4. Code review
5. Merge to main

---

## 📝 **License**

Private & Confidential - SC Lead Generation © 2025

---

## 🆘 **Support**

For questions or issues:
- **Email**: charlie.hajj@gmail.com / sarakaram25@gmail.com
- **GitHub Issues**: Create an issue in this repo

---

## 🎯 **Roadmap**

- [x] Phase 1: Foundation (Week 1)
- [ ] Phase 2: Data Cleaning (Week 2)
- [ ] Phase 3: AI Qualification (Week 3)
- [ ] Phase 4: Message Generation (Week 4)
- [ ] Phase 5: Outreach Automation (Week 5)
- [ ] Phase 6: Learning & Optimization (Week 6+)

---

**Built with ❤️ by Mahmoud Baassiri**

🚀 Let's automate lead generation for the aesthetics industry!
