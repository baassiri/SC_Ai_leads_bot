# 🚀 STARTUP GUIDE - Aesthetic LinkWizard Pro

## ✅ What You Have Now

All files are ready! Here's what's complete:

### **Backend:**
- ✅ `models.py` - Database models
- ✅ `db_manager.py` - Database operations
- ✅ `init_db.py` - Database initialization
- ✅ `app.py` - Flask web server
- ✅ `config.py` - Configuration

### **Frontend:**
- ✅ `base.html` - Base template (NEW!)
- ✅ `index.html` - Login/Settings page
- ✅ `dashboard.html` - Main dashboard
- ✅ `leads.html` - Leads management
- ✅ `messages.html` - Message generation
- ✅ `analytics.html` - Analytics dashboard

---

## 🎯 QUICK START (5 Steps)

### **Step 1: Set Up Virtual Environment**

Open Command Prompt in your project folder:

```bash
cd "C:\Users\wmmb\OneDrive\Desktop\SC_Ai_leads_bot"

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### **Step 2: Configure Environment Variables**

Create a `.env` file in your project root:

```bash
copy .env.example .env
```

Edit `.env` with your credentials:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this

# Database
DATABASE_URL=sqlite:///data/database.db

# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here

# LinkedIn Credentials (wait for Charlie to add you)
LINKEDIN_EMAIL=your-linkedin-email@example.com
LINKEDIN_PASSWORD=your-linkedin-password

# HubSpot (Phase 5 - leave disabled for now)
HUBSPOT_ENABLED=False
HUBSPOT_API_KEY=

# Security
DEBUG=True
CORS_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
```

---

### **Step 3: Initialize Database**

```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Initialize the database
python scripts/init_db.py
```

You should see:
```
🔧 Initializing SC AI Lead Generation Database...
==================================================
✅ All database tables created successfully!

📊 Seeding persona data...
  ✅ Created persona: Plastic Surgeon
  ✅ Created persona: Dermatologist
  ✅ Created persona: Med Spa Owner
  ✅ Created persona: Day Spa
  ✅ Created persona: Wellness Center
  ✅ Created persona: Aesthetic Clinic
✅ Persona seeding complete!

🎉 Database initialization complete!
```

---

### **Step 4: Start the Flask Server**

```bash
python backend/app.py
```

You should see:
```
🚀 Starting SC AI Lead Generation System...
==================================================
📊 Dashboard: http://localhost:5000/dashboard
🎯 Leads: http://localhost:5000/leads
✉️  Messages: http://localhost:5000/messages
📈 Analytics: http://localhost:5000/analytics
==================================================
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

---

### **Step 5: Open in Browser**

Visit: **http://localhost:5000/**

You'll see the login page where you can:
1. Enter LinkedIn credentials
2. Enter OpenAI API key
3. Test connections
4. Navigate to dashboard

---

## 📁 File Locations

Make sure all files are in the correct locations:

```
SC_Ai_leads_bot/
│
├── backend/
│   ├── app.py                    ✅ Flask server
│   ├── config.py                 ✅ Configuration
│   │
│   └── database/
│       ├── models.py             ✅ Database models
│       ├── db_manager.py         ✅ Database manager
│       └── __init__.py
│
├── frontend/
│   └── templates/
│       ├── base.html             ✅ NEW! Base template
│       ├── index.html            ✅ Login page
│       ├── dashboard.html        ✅ Dashboard
│       ├── leads.html            ✅ Leads page
│       ├── messages.html         ✅ Messages page
│       └── analytics.html        ✅ Analytics page
│
├── data/                         ✅ Auto-created
│   └── database.db              (created after init_db.py)
│
├── scripts/
│   └── init_db.py               ✅ Database setup
│
├── .env                          📝 CREATE THIS
├── .env.example                  ✅ Template
├── requirements.txt              ✅ Dependencies
└── README.md                     ✅ Documentation
```

---

## 🔧 Troubleshooting

### **Issue: "No module named 'flask'"**

**Solution:**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

### **Issue: "Unable to open database file"**

**Solution:**
```bash
# Create data directory
mkdir data

# Run init_db.py again
python scripts/init_db.py
```

---

### **Issue: "Port 5000 already in use"**

**Solution:**
```bash
# Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Or change port in app.py
# app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG)
```

---

### **Issue: Templates not found**

**Solution:**

Check that `app.py` has correct paths:
```python
app = Flask(__name__,
           template_folder='../frontend/templates',  # ✅ Correct
           static_folder='../frontend/static')        # ✅ Correct
```

---

## 🎯 Next Steps After Startup

Once the server is running:

### **Immediate Tasks:**
1. ✅ Visit http://localhost:5000/
2. ✅ Enter credentials in Settings
3. ✅ Test OpenAI connection
4. ✅ Upload Targets.docx (wait for Charlie to add you to LinkedIn first)

### **Phase 1 - Foundation (This Week):**
- [ ] Build LinkedIn scraper
- [ ] Test scraping with Sales Navigator
- [ ] Save leads to database
- [ ] View leads in dashboard

### **Phase 2 - Data Cleaning (Next Week):**
- [ ] Implement duplicate detection
- [ ] Add data validation
- [ ] Create manual review interface
- [ ] Match leads to personas

### **Phase 3 - AI Qualification (Week 3):**
- [ ] Integrate OpenAI for lead scoring
- [ ] Implement scoring algorithm
- [ ] Display AI scores in leads table

---

## 📊 Testing the System

### **Test 1: Database Connection**

```bash
python
>>> from backend.database.db_manager import db_manager
>>> stats = db_manager.get_dashboard_stats()
>>> print(stats)
```

### **Test 2: API Endpoints**

Open a new terminal:

```bash
# Test dashboard stats
curl http://localhost:5000/api/analytics/dashboard

# Test leads endpoint
curl http://localhost:5000/api/leads

# Test personas
curl http://localhost:5000/api/leads-by-persona
```

### **Test 3: Frontend Pages**

Visit each page and check for errors:
- http://localhost:5000/ (Login)
- http://localhost:5000/dashboard (Dashboard)
- http://localhost:5000/leads (Leads)
- http://localhost:5000/messages (Messages)
- http://localhost:5000/analytics (Analytics)

---

## 🔐 Security Notes

⚠️ **IMPORTANT:** Before deploying to production:

1. Change `SECRET_KEY` in `.env`
2. Set `DEBUG=False`
3. Use PostgreSQL instead of SQLite
4. Encrypt LinkedIn credentials
5. Add HTTPS/SSL certificates
6. Implement rate limiting
7. Add authentication system

---

## 📞 Need Help?

### **Common Commands:**

```bash
# Activate virtual environment
venv\Scripts\activate

# Start server
python backend/app.py

# Initialize database
python scripts/init_db.py

# Reset database (⚠️ DELETES ALL DATA)
python scripts/init_db.py --reset

# Check dependencies
pip list

# Install new package
pip install package-name
pip freeze > requirements.txt
```

---

## ✅ Success Checklist

Before moving to Phase 1 development:

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] .env file created with credentials
- [ ] Database initialized successfully
- [ ] Flask server running without errors
- [ ] All 5 pages load in browser
- [ ] No console errors in browser
- [ ] Bot start/stop buttons visible
- [ ] Personas count shows "6"
- [ ] Ready to build LinkedIn scraper!

---

## 🎉 You're Ready!

Everything is set up! The foundation is complete.

**Next step:** Build the LinkedIn scraper module to start collecting leads.

Just let me know when you're ready to start Phase 1 development! 🚀
