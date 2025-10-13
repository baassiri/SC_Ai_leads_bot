/**
 * Settings Page JavaScript
 */

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
});

/**
 * Load current settings from server
 */
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        
        if (response.ok) {
            const data = await response.json();
            
            // Populate form fields
            if (data.linkedin_email) {
                document.getElementById('linkedin_email').value = data.linkedin_email;
            }
            if (data.linkedin_password) {
                document.getElementById('linkedin_password').value = '••••••••'; // Masked
            }
            if (data.openai_api_key) {
                document.getElementById('openai_api_key').value = '••••••••'; // Masked
            }
            
            // Scraping settings
            if (data.max_leads) {
                document.getElementById('max_leads').value = data.max_leads;
            }
            if (data.scrape_delay) {
                document.getElementById('scrape_delay').value = data.scrape_delay;
            }
            if (data.sales_nav_enabled !== undefined) {
                document.getElementById('sales_nav_enabled').checked = data.sales_nav_enabled;
            }
            if (data.headless_mode !== undefined) {
                document.getElementById('headless_mode').checked = data.headless_mode;
            }
            
            // Messaging settings
            if (data.messages_per_hour) {
                document.getElementById('messages_per_hour').value = data.messages_per_hour;
            }
            if (data.connection_limit) {
                document.getElementById('connection_limit').value = data.connection_limit;
            }
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        showMessage('Error loading settings', 'error');
    }
}

/**
 * Save settings to server
 */
async function saveSettings() {
    try {
        // Get form values
        const settings = {
            linkedin_email: document.getElementById('linkedin_email').value.trim(),
            linkedin_password: document.getElementById('linkedin_password').value.trim(),
            openai_api_key: document.getElementById('openai_api_key').value.trim(),
            max_leads: parseInt(document.getElementById('max_leads').value),
            scrape_delay: parseFloat(document.getElementById('scrape_delay').value),
            sales_nav_enabled: document.getElementById('sales_nav_enabled').checked,
            headless_mode: document.getElementById('headless_mode').checked,
            messages_per_hour: parseInt(document.getElementById('messages_per_hour').value),
            connection_limit: parseInt(document.getElementById('connection_limit').value)
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
        const response = await fetch('/api/settings/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('Settings saved successfully!', 'success');
            
            // Reload settings to show masked passwords
            setTimeout(() => {
                loadSettings();
            }, 1000);
        } else {
            showMessage(result.message || 'Error saving settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('Error saving settings', 'error');
    }
}

/**
 * Test credentials
 */
async function testCredentials() {
    try {
        showMessage('Testing credentials...', 'info');
        
        const response = await fetch('/api/settings/test', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            let message = 'All credentials are valid!';
            
            if (result.details) {
                message += '\n\n';
                if (result.details.linkedin) {
                    message += '✅ LinkedIn: Connected\n';
                }
                if (result.details.openai) {
                    message += '✅ OpenAI: Connected\n';
                }
                if (result.details.sales_nav) {
                    message += '✅ Sales Navigator: Available\n';
                }
            }
            
            showMessage(message, 'success');
        } else {
            showMessage(result.message || 'Credential test failed', 'error');
        }
    } catch (error) {
        console.error('Error testing credentials:', error);
        showMessage('Error testing credentials', 'error');
    }
}

/**
 * Show status message
 */
function showMessage(message, type = 'info') {
    const messageDiv = document.getElementById('statusMessage');
    
    messageDiv.textContent = message;
    messageDiv.className = `alert alert-${type}`;
    messageDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}