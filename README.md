# 🤖 LinkedIn AI Leads Bot

An intelligent LinkedIn automation tool that uses AI to generate personalized messages and automate lead outreach campaigns.

## 📋 Features

- **AI-Powered Message Generation**: Automatically creates personalized connection requests using OpenAI
- **Lead Management**: Import, score, and manage leads from CSV files
- **Smart Scheduling**: Optimal timing for message delivery with human-like delays
- **LinkedIn Automation**: Automated connection requests with personalized messages
- **Session Management**: Persistent LinkedIn login sessions with cookie storage
- **Analytics Dashboard**: Track campaign performance and engagement metrics
- **Database Integration**: SQLite database for tracking leads, messages, and campaigns

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- LinkedIn account
- OpenAI API key

### Installation

#### Windows:
1. Clone the repository:
```bash
git clone https://github.com/baassiri/SC_Ai_leads_bot.git
cd SC_Ai_leads_bot
```

2. Run the setup script:
```bash
SETUP_WINDOWS.bat
```

3. Create your `.env` file:
```bash
copy env.template .env
```

4. Edit `.env` and add your credentials:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
OPENAI_API_KEY=sk-your-api-key-here
```

5. Start the application:
```bash
START_WINDOWS.bat
```

#### Mac/Linux:
1. Clone the repository:
```bash
git clone https://github.com/baassiri/SC_Ai_leads_bot.git
cd SC_Ai_leads_bot
```

2. Run the setup script:
```bash
chmod +x SETUP_MAC.sh
./SETUP_MAC.sh
```

3. Create your `.env` file:
```bash
cp env.template .env
```

4. Edit `.env` and add your credentials:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
OPENAI_API_KEY=sk-your-api-key-here
```

5. Start the application:
```bash
chmod +x START_MAC.sh
./START_MAC.sh
```

### Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## 📖 Usage Guide

### 1. Login to LinkedIn
- Click the "Login to LinkedIn" button on the Messages page
- Complete the login (CAPTCHA/2FA if required)
- Session will be saved for future use

### 2. Import Leads
- Navigate to the Leads page
- Upload a CSV file with lead information
- Required columns: `name`, `title`, `company`, `linkedin_url`

### 3. Generate Messages
- AI will automatically generate personalized messages for each lead
- Review and approve messages before sending
- Edit messages if needed

### 4. Send Messages
- Click "Send Approved Messages" to start the campaign
- Messages are sent with randomized delays (2-5 minutes) to appear human-like
- Track progress in real-time

### 5. Monitor Analytics
- View campaign performance on the Analytics page
- Track connection acceptance rates
- Monitor response rates and engagement

## 🏗️ Project Structure

```
SC_Ai_leads_bot/
├── backend/
│   ├── api/                 # API routes
│   ├── ai_engine/           # AI message generation
│   ├── automation/          # LinkedIn automation
│   ├── database/            # Database models and migrations
│   ├── scrapers/            # LinkedIn scrapers
│   └── app.py              # Main Flask application
├── frontend/
│   ├── static/             # CSS, JS, images
│   └── templates/          # HTML templates
├── data/                   # User data and uploads
├── scripts/                # Utility scripts
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# OpenAI API
OPENAI_API_KEY=sk-your-api-key-here

# Application Settings
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Optional: Sales Navigator
SALES_NAV_ENABLED=false
```

### Rate Limiting

To avoid LinkedIn restrictions, the bot implements:
- Random delays between messages (2-5 minutes)
- Maximum messages per day (configurable)
- Human-like behavior patterns

## 🛠️ Advanced Features

### A/B Testing
Test different message variations to optimize response rates

### Persona Analysis
AI analyzes lead profiles to customize messaging approach

### Lead Scoring
Automatically scores leads based on relevance and engagement potential

### Queue Management
Schedule messages for optimal sending times

## 🐛 Troubleshooting

### Common Issues

**Problem: Login fails**
- Solution: Verify credentials in `.env` file, complete CAPTCHA if prompted

**Problem: Messages not sending**
- Solution: Check that messages are approved and LinkedIn session is active

**Problem: ChromeDriver error**
- Solution: Ensure Chrome browser is installed and updated

**Problem: OpenAI API errors**
- Solution: Verify API key is valid and has sufficient credits

### Database Reset

If you need to reset the database:
```bash
python clear_db.py
python init_db.py
```

## 📊 Database Schema

The application uses SQLite with the following main tables:
- `leads` - Lead information and status
- `messages` - Generated messages and their status
- `campaigns` - Campaign tracking
- `ab_tests` - A/B test results
- `message_schedule` - Scheduled message queue

## 🔒 Security Notes

- Never commit `.env` file to git (already in `.gitignore`)
- Store credentials securely
- Use environment variables for sensitive data
- Regularly rotate API keys
- Be cautious with LinkedIn automation to avoid account restrictions

## 📝 Best Practices

1. **Start Small**: Test with 5-10 leads before scaling up
2. **Review Messages**: Always review AI-generated messages before sending
3. **Monitor Activity**: Check LinkedIn for warnings or restrictions
4. **Respect Limits**: Don't exceed LinkedIn's connection request limits
5. **Personalize**: Customize messages for better response rates

## 🤝 Contributing

This is a private project. For issues or questions, contact the repository owner.

## ⚖️ Legal Disclaimer

This tool is for educational and professional networking purposes only. Users are responsible for:
- Complying with LinkedIn's Terms of Service
- Following applicable laws and regulations
- Using the tool ethically and responsibly

Automated actions on LinkedIn may violate their terms of service. Use at your own risk.

## 📧 Support

For questions or issues, please contact the project maintainer.

## 🔄 Updates

Check the repository regularly for updates and new features.

---

**Version**: 1.0.0  
**Last Updated**: October 2024  
**License**: Private Use Only