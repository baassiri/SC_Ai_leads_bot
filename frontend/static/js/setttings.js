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
async function saveSettings() {
    try {
        // Get form values
        const settings = {
            linkedin_email: document.getElementById('linkedin_email').value.trim(),
            linkedin_password: document.getElementById('linkedin_password').value.trim(),
            openai_api_key: document.getElementById('openai_api_key').value.trim(),
            sales_nav_enabled: document.getElementById('sales_nav_enabled') ? 
                document.getElementById('sales_nav_enabled').checked : false
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
        
        // Send to server - FIXED ENDPOINT
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
 * Test LinkedIn credentials
 */
async function testLinkedInConnection() {
    try {
        showMessage('Testing LinkedIn connection...', 'info');
        
        const response = await fetch('/api/auth/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ service: 'linkedin' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('✅ ' + result.message, 'success');
        } else {
            showMessage('❌ ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error testing LinkedIn:', error);
        showMessage('Error testing LinkedIn connection', 'error');
    }
}

/**
 * Test OpenAI credentials
 */
async function testOpenAIConnection() {
    try {
        showMessage('Testing OpenAI connection...', 'info');
        
        const response = await fetch('/api/auth/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ service: 'openai' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('✅ ' + result.message, 'success');
        } else {
            showMessage('❌ ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Error testing OpenAI:', error);
        showMessage('Error testing OpenAI connection', 'error');
    }
}

/**
 * Test all credentials
 */
async function testConnection() {
    try {
        showMessage('Testing all connections...', 'info');
        
        // Test LinkedIn
        const linkedinResponse = await fetch('/api/auth/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service: 'linkedin' })
        });
        const linkedinResult = await linkedinResponse.json();
        
        // Test OpenAI
        const openaiResponse = await fetch('/api/auth/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service: 'openai' })
        });
        const openaiResult = await openaiResponse.json();
        
        // Build message
        let message = '';
        if (linkedinResult.success) {
            message += '✅ LinkedIn: ' + linkedinResult.message + '\n';
        } else {
            message += '❌ LinkedIn: ' + linkedinResult.message + '\n';
        }
        
        if (openaiResult.success) {
            message += '✅ OpenAI: ' + openaiResult.message;
        } else {
            message += '❌ OpenAI: ' + openaiResult.message;
        }
        
        const allSuccess = linkedinResult.success && openaiResult.success;
        showMessage(message, allSuccess ? 'success' : 'error');
        
    } catch (error) {
        console.error('Error testing credentials:', error);
        showMessage('Error testing credentials', 'error');
    }
}

/**
 * Reset form
 */
function resetForm() {
    if (confirm('Reset all settings to default?')) {
        document.getElementById('linkedin_email').value = '';
        document.getElementById('linkedin_password').value = '';
        document.getElementById('openai_api_key').value = '';
        
        if (document.getElementById('sales_nav_enabled')) {
            document.getElementById('sales_nav_enabled').checked = false;
        }
        
        showMessage('Form reset', 'info');
    }
}

/**
 * Show status message
 */
function showMessage(message, type = 'info') {
    // Try to find an existing message container
    let messageDiv = document.getElementById('statusMessage');
    
    if (!messageDiv) {
        // Create one if it doesn't exist
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
    
    // Set colors based on type
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
    
    // Auto-hide after 5 seconds
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