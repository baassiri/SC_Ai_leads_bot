// Messages Page JavaScript
let linkedInLoggedIn = false;
let linkedInUserName = '';

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('Messages page loaded');
    
    // Check LinkedIn login status first
    checkLinkedInStatus();
    
    // Load message stats
    loadMessageStats();
    
    // Load messages
    loadMessages();
    
    // Setup event listeners
    setupEventListeners();
});

function setupEventListeners() {
    // LinkedIn Login
    document.getElementById('linkedin-login-btn').addEventListener('click', loginToLinkedIn);
    
    // LinkedIn Logout
    document.getElementById('linkedin-logout-btn').addEventListener('click', logoutFromLinkedIn);
    
    // Generate Messages
    document.getElementById('generate-messages-btn').addEventListener('click', generateMessages);
    
    // Send Messages
    document.getElementById('send-messages-btn').addEventListener('click', sendApprovedMessages);
    
    // Filters
    document.getElementById('apply-filters-btn').addEventListener('click', applyFilters);
    document.getElementById('status-filter').addEventListener('change', applyFilters);
}

// ============================================================================
// LINKEDIN CONNECTION
// ============================================================================

async function checkLinkedInStatus() {
    console.log('Checking LinkedIn login status...');
    
    const statusDiv = document.getElementById('linkedin-status');
    const loginBtn = document.getElementById('linkedin-login-btn');
    const logoutBtn = document.getElementById('linkedin-logout-btn');
    const sendBtn = document.getElementById('send-messages-btn');
    
    try {
        const response = await fetch('/api/linkedin/status');
        const data = await response.json();
        
        if (data.logged_in) {
            // User is logged in
            linkedInLoggedIn = true;
            linkedInUserName = data.user_name || 'LinkedIn User';
            
            statusDiv.innerHTML = `
                <div class="status-connected">
                    <span class="status-icon">✅</span>
                    <span class="status-text">Connected as: <strong>${linkedInUserName}</strong></span>
                </div>
            `;
            
            // Show logout button, hide login
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'inline-block';
            sendBtn.disabled = false;
            
        } else {
            // User is not logged in
            linkedInLoggedIn = false;
            linkedInUserName = '';
            
            statusDiv.innerHTML = `
                <div class="status-disconnected">
                    <span class="status-icon">⚠️</span>
                    <span class="status-text">Not connected to LinkedIn</span>
                </div>
            `;
            
            // Show login button, hide logout
            loginBtn.style.display = 'inline-block';
            logoutBtn.style.display = 'none';
            sendBtn.disabled = true;
        }
        
    } catch (error) {
        console.error('Error checking LinkedIn status:', error);
        
        linkedInLoggedIn = false;
        
        statusDiv.innerHTML = `
            <div class="status-error">
                <span class="status-icon">❌</span>
                <span class="status-text">Unable to check LinkedIn status</span>
            </div>
        `;
        
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        sendBtn.disabled = true;
    }
}

async function loginToLinkedIn() {
    console.log('Starting LinkedIn login...');
    
    const statusDiv = document.getElementById('linkedin-status');
    const loginBtn = document.getElementById('linkedin-login-btn');
    
    // Show loading
    statusDiv.innerHTML = `
        <div class="status-loading">
            <span class="spinner"></span>
            <span>Logging into LinkedIn... This may take a moment.</span>
        </div>
    `;
    
    loginBtn.disabled = true;
    
    try {
        const response = await fetch('/api/linkedin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            
            // Check status again to update UI
            setTimeout(() => {
                checkLinkedInStatus();
            }, 1000);
            
        } else {
            throw new Error(data.error || 'Login failed');
        }
        
    } catch (error) {
        console.error('LinkedIn login error:', error);
        showNotification('❌ Login failed: ' + error.message, 'error');
        
        statusDiv.innerHTML = `
            <div class="status-error">
                <span class="status-icon">❌</span>
                <span class="status-text">Login failed: ${error.message}</span>
            </div>
        `;
        
        loginBtn.disabled = false;
    }
}

async function logoutFromLinkedIn() {
    console.log('Logging out from LinkedIn...');
    
    try {
        const response = await fetch('/api/linkedin/close', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Logged out successfully', 'success');
            checkLinkedInStatus();
        }
        
    } catch (error) {
        console.error('Logout error:', error);
        showNotification('❌ Logout failed: ' + error.message, 'error');
    }
}

// ============================================================================
// MESSAGE STATS
// ============================================================================

async function loadMessageStats() {
    try {
        const response = await fetch('/api/messages/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('draft-count').textContent = data.stats.draft || 0;
            document.getElementById('approved-count').textContent = data.stats.approved || 0;
            document.getElementById('sent-count').textContent = data.stats.sent || 0;
            
            // Calculate reply rate (placeholder - you'll need to add this to backend)
            const replyRate = 0; // TODO: Get from backend
            document.getElementById('reply-rate').textContent = replyRate + '%';
        }
        
    } catch (error) {
        console.error('Error loading message stats:', error);
    }
}

// ============================================================================
// LOAD MESSAGES
// ============================================================================

async function loadMessages(statusFilter = null) {
    const container = document.getElementById('messages-container');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading messages...</p>
        </div>
    `;
    
    try {
        let url = '/api/messages';
        if (statusFilter) {
            url += `?status=${statusFilter}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.messages.length > 0) {
            displayMessages(data.messages);
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <p>📭 No messages found</p>
                    <button class="btn btn-primary" onclick="generateMessages()">
                        Generate Messages
                    </button>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading messages:', error);
        container.innerHTML = `
            <div class="error-state">
                <p>❌ Error loading messages: ${error.message}</p>
                <button class="btn btn-secondary" onclick="loadMessages()">Retry</button>
            </div>
        `;
    }
}

function displayMessages(messages) {
    const container = document.getElementById('messages-container');
    
    let html = '<div class="messages-list">';
    
    messages.forEach(message => {
        const statusBadge = getStatusBadge(message.status);
        const variantBadge = message.variant ? `<span class="badge badge-variant">Variant ${message.variant}</span>` : '';
        
        html += `
            <div class="message-card" data-id="${message.id}">
                <div class="message-header">
                    <div class="message-meta">
                        <h3>${message.lead_name || 'Unknown Lead'}</h3>
                        <p class="message-company">${message.lead_title || ''} ${message.lead_company ? 'at ' + message.lead_company : ''}</p>
                    </div>
                    <div class="message-badges">
                        ${statusBadge}
                        ${variantBadge}
                    </div>
                </div>
                
                <div class="message-content">
                    <p>${message.content}</p>
                </div>
                
                <div class="message-actions">
                    ${getMessageActions(message)}
                </div>
                
                <div class="message-footer">
                    <small>Created: ${formatDate(message.created_at)}</small>
                    ${message.sent_at ? `<small>Sent: ${formatDate(message.sent_at)}</small>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function getStatusBadge(status) {
    const badges = {
        'draft': '<span class="badge badge-draft">📝 Draft</span>',
        'approved': '<span class="badge badge-approved">✅ Approved</span>',
        'sent': '<span class="badge badge-sent">📨 Sent</span>',
        'failed': '<span class="badge badge-failed">❌ Failed</span>'
    };
    
    return badges[status] || '<span class="badge">Unknown</span>';
}

function getMessageActions(message) {
    if (message.status === 'draft') {
        return `
            <button class="btn btn-sm btn-success" onclick="approveMessage(${message.id})">
                ✅ Approve
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteMessage(${message.id})">
                🗑️ Delete
            </button>
        `;
    } else if (message.status === 'approved') {
        return `
            <button class="btn btn-sm btn-primary" onclick="sendSingleMessage(${message.id})">
                📨 Send Now
            </button>
            <button class="btn btn-sm btn-secondary" onclick="unapproveMessage(${message.id})">
                ↩️ Back to Draft
            </button>
        `;
    } else if (message.status === 'sent') {
        return '<span class="text-muted">Message sent ✓</span>';
    }
    
    return '';
}

// ============================================================================
// GENERATE MESSAGES
// ============================================================================

async function generateMessages() {
    const btn = document.getElementById('generate-messages-btn');
    const statusDiv = document.getElementById('action-status');
    const statusMessage = document.getElementById('action-message');
    
    // Disable button
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    
    // Show status
    statusDiv.style.display = 'block';
    statusMessage.textContent = 'Generating A/B/C message variants for top leads... This may take a minute.';
    
    try {
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // Add any specific lead IDs if needed
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusMessage.textContent = `✅ ${data.message}`;
            showNotification('✅ ' + data.message, 'success');
            
            // Reload messages and stats
            setTimeout(() => {
                loadMessages();
                loadMessageStats();
                statusDiv.style.display = 'none';
            }, 2000);
            
        } else {
            throw new Error(data.message || 'Generation failed');
        }
        
    } catch (error) {
        console.error('Error generating messages:', error);
        statusMessage.textContent = '❌ Error: ' + error.message;
        showNotification('❌ Generation failed: ' + error.message, 'error');
        
    } finally {
        btn.disabled = false;
        btn.textContent = '🎨 Generate Messages for Top Leads';
    }
}

// ============================================================================
// SEND MESSAGES
// ============================================================================

async function sendApprovedMessages() {
    if (!linkedInLoggedIn) {
        showNotification('⚠️ Please login to LinkedIn first', 'warning');
        return;
    }
    
    const btn = document.getElementById('send-messages-btn');
    const statusDiv = document.getElementById('action-status');
    const statusMessage = document.getElementById('action-message');
    
    // Confirm
    const confirmed = confirm('Send all approved messages to LinkedIn? This will send connection requests with personalized messages.');
    if (!confirmed) return;
    
    // Disable button
    btn.disabled = true;
    btn.textContent = '⏳ Sending...';
    
    // Show status
    statusDiv.style.display = 'block';
    statusMessage.textContent = '📨 Sending messages to LinkedIn... This may take several minutes.';
    
    try {
        const response = await fetch('/api/linkedin/send-messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusMessage.innerHTML = `
                <strong>✅ Sending Complete!</strong><br>
                📨 Sent: ${data.sent}<br>
                ❌ Failed: ${data.failed}<br>
                ⏭️ Skipped: ${data.skipped}
            `;
            
            showNotification(`✅ Sent ${data.sent} messages!`, 'success');
            
            // Reload messages and stats
            setTimeout(() => {
                loadMessages();
                loadMessageStats();
            }, 2000);
            
        } else {
            throw new Error(data.error || 'Sending failed');
        }
        
    } catch (error) {
        console.error('Error sending messages:', error);
        statusMessage.textContent = '❌ Error: ' + error.message;
        showNotification('❌ Sending failed: ' + error.message, 'error');
        
    } finally {
        btn.disabled = false;
        btn.textContent = '📨 Send Approved Messages';
    }
}

async function sendSingleMessage(messageId) {
    if (!linkedInLoggedIn) {
        showNotification('⚠️ Please login to LinkedIn first', 'warning');
        return;
    }
    
    const confirmed = confirm('Send this message now?');
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}/send`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message sent!', 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.message || 'Failed to send');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('❌ ' + error.message, 'error');
    }
}

// ============================================================================
// MESSAGE ACTIONS
// ============================================================================

async function approveMessage(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message approved!', 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.message || 'Approval failed');
        }
        
    } catch (error) {
        console.error('Error approving message:', error);
        showNotification('❌ ' + error.message, 'error');
    }
}

async function unapproveMessage(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'draft' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Moved back to draft', 'success');
            loadMessages();
            loadMessageStats();
        }
        
    } catch (error) {
        console.error('Error updating message:', error);
        showNotification('❌ ' + error.message, 'error');
    }
}

async function deleteMessage(messageId) {
    const confirmed = confirm('Delete this message? This cannot be undone.');
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message deleted', 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.message || 'Delete failed');
        }
        
    } catch (error) {
        console.error('Error deleting message:', error);
        showNotification('❌ ' + error.message, 'error');
    }
}

// ============================================================================
// FILTERS
// ============================================================================

function applyFilters() {
    const status = document.getElementById('status-filter').value;
    loadMessages(status || null);
}

// ============================================================================
// UTILITIES
// ============================================================================

function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showNotification(message, type = 'info') {
    // Simple notification (you can enhance this with a proper notification system)
    alert(message);
}