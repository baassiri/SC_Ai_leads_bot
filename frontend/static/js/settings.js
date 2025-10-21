/**
 * Settings Page JavaScript - FIXED
 */

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Settings page loaded');
});

/**
 * Save settings to server
 */
async function saveSettings(event) {
    if (event) event.preventDefault();
    
    try {
        // Get form values - FIXED IDs to match HTML
        const settings = {
            linkedin_email: document.getElementById('li-email').value.trim(),
            linkedin_password: document.getElementById('li-password').value.trim(),
            openai_api_key: document.getElementById('openai-key').value.trim(),
            sales_nav_enabled: document.getElementById('sales-nav-enabled') ? 
                document.getElementById('sales-nav-enabled').checked : false
        };
        
        // Validate
        if (!settings.linkedin_email || !settings.linkedin_password) {
            showMessage('LinkedIn credentials are required', 'error');
            return;
        }
        
        if (!settings.openai_api_key) {
            showMessage('OpenAI API key is required', 'error');
            return;
        }
        
        // Show loading
        showMessage('Saving settings...', 'info');
        
        // Send to server
        const response = await fetch('/api/auth/save-credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message || 'Settings saved successfully!', 'success');
        } else {
            showMessage(result.message || 'Error saving settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('Error saving settings: ' + error.message, 'error');
    }
}

/**
 * Test connection
 */
async function testConnection() {
    try {
        showMessage('Testing connections...', 'info');
        
        const response = await fetch('/api/auth/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service: 'all' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('SUCCESS: ' + result.message, 'success');
        } else {
            showMessage('ERROR: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error testing connection:', error);
        showMessage('Error testing connection', 'error');
    }
}

/**
 * Show status message
 */
function showMessage(message, type = 'info') {
    let messageDiv = document.getElementById('statusMessage');
    
    if (!messageDiv) {
        messageDiv = document.createElement('div');
        messageDiv.id = 'statusMessage';
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.padding = '15px 20px';
        messageDiv.style.borderRadius = '8px';
        messageDiv.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        messageDiv.style.maxWidth = '400px';
        document.body.appendChild(messageDiv);
    }
    
    const colors = {
        'success': { bg: '#10b981', text: '#fff' },
        'error': { bg: '#ef4444', text: '#fff' },
        'info': { bg: '#3b82f6', text: '#fff' },
        'warning': { bg: '#f59e0b', text: '#fff' }
    };
    
    const color = colors[type] || colors.info;
    messageDiv.style.backgroundColor = color.bg;
    messageDiv.style.color = color.text;
    messageDiv.textContent = message;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            messageDiv.style.display = 'none';
            messageDiv.style.opacity = '1';
        }, 300);
    }, 5000);
}

console.log('Settings.js loaded successfully');