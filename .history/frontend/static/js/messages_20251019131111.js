// Messages Page JavaScript - FIXED: Wait for templates before showing modal
let linkedInLoggedIn = false;
let linkedInUserName = '';
let availableTemplates = [];
let pendingLeadIds = [];
let templatesLoaded = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Messages page loaded');
    checkLinkedInStatus();
    loadMessageStats();
    loadMessages();
    setupEventListeners();
    
    // Load templates THEN check for approval redirect
    loadTemplates().then(() => {
        console.log('✅ Templates loaded, checking for approval redirect');
        checkForApprovalRedirect();
    });
});

function setupEventListeners() {
    document.getElementById('linkedin-login-btn').addEventListener('click', loginToLinkedIn);
    document.getElementById('linkedin-logout-btn').addEventListener('click', logoutFromLinkedIn);
    document.getElementById('generate-messages-btn').addEventListener('click', generateMessages);
    document.getElementById('send-messages-btn').addEventListener('click', sendApprovedMessages);
    document.getElementById('apply-filters-btn').addEventListener('click', applyFilters);
    document.getElementById('status-filter').addEventListener('change', applyFilters);
}

// ============================================================================
// CHECK FOR APPROVAL REDIRECT FROM LEADS PAGE
// ============================================================================

function checkForApprovalRedirect() {
    const urlParams = new URLSearchParams(window.location.search);
    const isApproval = urlParams.get('approve') === 'true';
    
    if (isApproval) {
        console.log('🎯 Redirected from Leads page for approval');
        
        const storedIds = sessionStorage.getItem('selected_lead_ids');
        
        if (storedIds) {
            pendingLeadIds = JSON.parse(storedIds);
            console.log(`📝 Found ${pendingLeadIds.length} leads to approve:`, pendingLeadIds);
            sessionStorage.removeItem('selected_lead_ids');
            
            // Show modal immediately after templates are loaded
            setTimeout(() => {
                showTemplatePickerForApproval();
            }, 300);
        } else {
            alert('⚠️ No leads selected. Please go back to Leads page.');
        }
    }
}

function showTemplatePickerForApproval() {
    console.log('📋 Templates available:', availableTemplates.length);
    
    // Always show the template input modal
    showTemplateInputModal();
}

function showTemplateInputModal() {
    const modal = document.createElement('div');
    modal.id = 'approval-template-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 700px; max-height: 90vh; overflow-y: auto;">
            <h2 style="margin-top: 0; color: #1a73e8;">🎨 Create Message Template</h2>
            <p style="color: #666;">Generating messages for <strong>${pendingLeadIds.length} approved lead${pendingLeadIds.length !== 1 ? 's' : ''}</strong></p>
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #ddd;">
            
            <div style="margin: 20px 0;">
                <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #333;">
                    Enter Your Message Template:
                </label>
                <textarea 
                    id="modal-template-input" 
                    placeholder="Example: Hey {name}, saw you're at {company}. Let's connect!"
                    style="width: 100%; min-height: 120px; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; font-family: Arial, sans-serif; resize: vertical;"
                ></textarea>
                <small style="display: block; margin-top: 8px; color: #666;">
                    💡 Use placeholders: {name}, {company}, {title}
                </small>
            </div>
    `;
    
    // Show saved templates if any exist
    if (availableTemplates.length > 0) {
        html += `
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #ddd;">
            <div style="margin: 20px 0;">
                <h3 style="margin-bottom: 15px; font-size: 16px; color: #333;">Or select a saved template:</h3>
        `;
        
        availableTemplates.forEach(t => {
            html += `
                <div style="border: 1px solid #ddd; padding: 12px; margin: 8px 0; border-radius: 6px; cursor: pointer; transition: all 0.2s; background: #f9f9f9;"
                     onmouseover="this.style.borderColor='#1a73e8'; this.style.backgroundColor='#e8f0fe';"
                     onmouseout="this.style.borderColor='#ddd'; this.style.backgroundColor='#f9f9f9';"
                     onclick="document.getElementById('modal-template-input').value = \`${t.template.replace(/`/g, '\\`')}\`; this.style.borderColor='#1a73e8'; this.style.backgroundColor='#e8f0fe';">
                    <p style="margin: 0; font-size: 13px; color: #333;">${t.template}</p>
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    html += `
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #ddd;">
            
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button 
                    style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600;"
                    onclick="cancelApprovalFlow()">
                    ❌ Cancel
                </button>
                <button 
                    style="background: #6c757d; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600;"
                    onclick="generateWithoutTemplate()">
                    ⚡ Generate Without Template
                </button>
                <button 
                    style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600;"
                    onclick="generateWithCustomTemplate()">
                    ✅ Generate with Template
                </button>
            </div>
        </div>
    `;
    
    modal.innerHTML = html;
    document.body.appendChild(modal);
    
    // Focus on textarea
    setTimeout(() => {
        document.getElementById('modal-template-input').focus();
    }, 100);
}

window.generateWithCustomTemplate = function() {
    const templateText = document.getElementById('modal-template-input').value.trim();
    
    if (!templateText) {
        alert('⚠️ Please enter a template message first!');
        return;
    }
    
    console.log('🎨 Using custom template:', templateText);
    closeApprovalModal();
    
    // Save template first, then generate
    saveAndGenerateWithTemplate(templateText);
};

window.generateWithoutTemplate = function() {
    const confirm = window.confirm('Generate messages without a template?\n\nAI will create completely original messages for each lead.');
    
    if (confirm) {
        closeApprovalModal();
        generateMessagesForApprovedLeads(null);
    }
};

async function saveAndGenerateWithTemplate(templateText) {
    try {
        // Save the template
        const saveResponse = await fetch('/api/templates/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({template: templateText})
        });
        
        const saveData = await saveResponse.json();
        
        if (saveData.success) {
            console.log('✅ Template saved with ID:', saveData.template_id);
            // Generate with the saved template
            generateMessagesForApprovedLeads(saveData.template_id);
        } else {
            throw new Error('Failed to save template');
        }
        
    } catch (error) {
        console.error('Error saving template:', error);
        alert('❌ Error saving template. Generating without template instead.');
        generateMessagesForApprovedLeads(null);
    }
}

function cancelApprovalFlow() {
    closeApprovalModal();
    pendingLeadIds = [];
    alert('❌ Cancelled. No messages generated.');
}

function closeApprovalModal() {
    const modal = document.getElementById('approval-template-modal');
    if (modal) {
        modal.remove();
    }
}

// REPLACE THE generateMessages() FUNCTION IN messages.js WITH THIS:

async function generateMessages() {
    const btn = document.getElementById('generate-messages-btn');
    const statusDiv = document.getElementById('action-status');
    const statusMessage = document.getElementById('action-message');
    
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    
    statusDiv.style.display = 'block';
    statusMessage.textContent = 'Fetching qualified leads...';
    
    try {
        // STEP 1: Fetch qualified leads (status='qualified' or score >= 70)
        const leadsResponse = await fetch('/api/leads/top?min_score=70&limit=10');
        const leadsData = await leadsResponse.json();
        
        if (!leadsData.success || !leadsData.leads || leadsData.leads.length === 0) {
            throw new Error('No qualified leads found. Please approve some leads first.');
        }
        
        // Extract lead IDs
        const leadIds = leadsData.leads.map(lead => lead.id);
        
        console.log(`🎯 Found ${leadIds.length} qualified leads:`, leadIds);
        
        statusMessage.textContent = `Generating A/B/C message variants for ${leadIds.length} leads... This may take a minute.`;
        
        // STEP 2: Generate messages for these leads
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lead_ids: leadIds
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusMessage.textContent = `✅ ${data.message}`;
            showNotification('✅ ' + data.message, 'success');
            
            setTimeout(() => {
                loadMessages();
                loadMessageStats();
                statusDiv.style.display = 'none';
            }, 2000);
            
        } else {
            throw new Error(data.error || data.message || 'Generation failed');
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
// TEMPLATE MANAGEMENT
// ============================================================================

async function saveTemplate() {
    const templateText = document.getElementById('templateText').value.trim();
    
    if (!templateText) {
        showNotification('Please enter a template message', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/templates/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({template: templateText})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Template saved!', 'success');
            document.getElementById('templateText').value = '';
            loadTemplates();
        } else {
            throw new Error(data.message || 'Failed to save template');
        }
    } catch (error) {
        console.error('Error saving template:', error);
        showNotification('❌ ' + error.message, 'error');
    }
}

async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const data = await response.json();
        
        const container = document.getElementById('savedTemplates');
        
        if (data.success && data.templates && data.templates.length > 0) {
            availableTemplates = data.templates;
            templatesLoaded = true;
            
            if (container) {
                container.style.display = 'block';
                
                let html = '<h6 class="font-medium mb-2">Saved Templates:</h6>';
                
                data.templates.forEach(t => {
                    html += `
                        <div class="template-item">
                            <p>${t.template}</p>
                            <div class="flex gap-2">
                                <button class="btn btn-sm btn-secondary" onclick="useTemplate(${t.id})">📋 Use</button>
                                <button class="btn btn-sm btn-primary" onclick="generateWithTemplate(${t.id})">🎨 Generate Messages</button>
                                <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${t.id})">🗑️ Delete</button>
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
            }
        } else {
            availableTemplates = [];
            templatesLoaded = true;
            if (container) {
                container.style.display = 'none';
            }
        }
        
        console.log('✅ Loaded', availableTemplates.length, 'templates');
        
    } catch (error) {
        console.error('Error loading templates:', error);
        templatesLoaded = true;
    }
}

async function useTemplate(templateId) {
    try {
        const response = await fetch(`/api/templates/${templateId}`);
        const data = await response.json();
        
        if (data.success && data.template) {
            document.getElementById('templateText').value = data.template.template;
            showNotification('✅ Template loaded!', 'success');
        }
    } catch (error) {
        console.error('Error loading template:', error);
    }
}

async function deleteTemplate(templateId) {
    if (!confirm('Delete this template?')) return;
    
    try {
        const response = await fetch(`/api/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Template deleted', 'success');
            loadTemplates();
        }
    } catch (error) {
        console.error('Error deleting template:', error);
        showNotification('❌ Failed to delete template', 'error');
    }
}

async function generateWithTemplate(templateId) {
    const btn = document.getElementById('generate-messages-btn');
    const statusDiv = document.getElementById('action-status');
    const statusMessage = document.getElementById('action-message');
    
    const template = availableTemplates.find(t => t.id === templateId);
    const templatePreview = template ? template.template.substring(0, 50) + '...' : 'Template';
    
    btn.disabled = true;
    btn.textContent = '⏳ Generating with template...';
    
    statusDiv.style.display = 'block';
    statusMessage.textContent = `🎨 Using template: "${templatePreview}"\nAI is personalizing for each lead...`;
    
    try {
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ template_id: templateId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusMessage.textContent = `✅ ${data.message}`;
            showNotification('✅ AI personalized your template for each lead!', 'success');
            
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
// EDIT MESSAGE
// ============================================================================

async function editMessage(messageId) {
    const newContent = prompt('Edit message content:');
    
    if (!newContent || newContent.trim() === '') {
        return;
    }
    
    try {
        const response = await fetch(`/api/messages/${messageId}/edit`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: newContent.trim()})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message updated!', 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.message || 'Failed to update message');
        }
    } catch (error) {
        console.error('Error editing message:', error);
        showNotification('❌ ' + error.message, 'error');
    }
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
            linkedInLoggedIn = true;
            linkedInUserName = data.user_name || 'LinkedIn User';
            
            statusDiv.innerHTML = `
                <div class="status-connected">
                    <span class="status-icon">✅</span>
                    <span class="status-text">Connected as: <strong>${linkedInUserName}</strong></span>
                </div>
            `;
            
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'inline-block';
            sendBtn.disabled = false;
            
        } else {
            linkedInLoggedIn = false;
            linkedInUserName = '';
            
            statusDiv.innerHTML = `
                <div class="status-disconnected">
                    <span class="status-icon">⚠️</span>
                    <span class="status-text">Not connected to LinkedIn</span>
                </div>
            `;
            
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
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            setTimeout(() => checkLinkedInStatus(), 1000);
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
            
            const replyRate = 0;
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
                    <p>🔭 No messages found</p>
                    <button class="btn btn-primary" onclick="window.location.href='/leads'">
                        Go to Leads & Approve Some
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
            <button class="btn btn-sm btn-warning" onclick="editMessage(${message.id})">
                ✏️ Edit
            </button>
            <button class="btn btn-sm btn-success" onclick="approveMessage(${message.id})">
                ✅ Approve
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteMessage(${message.id})">
                🗑️ Delete
            </button>
        `;
    } else if (message.status === 'approved') {
        return `
            <button class="btn btn-sm btn-warning" onclick="editMessage(${message.id})">
                ✏️ Edit
            </button>
            <button class="btn btn-sm btn-primary" onclick="sendSingleMessage(${message.id})">
                📨 Send Now
            </button>
            <button class="btn btn-sm btn-secondary" onclick="unapproveMessage(${message.id})">
                ↩️ Back to Draft
            </button>
        `;
    } else if (message.status === 'sent') {
        return '<span class="text-muted">Message sent ✔</span>';
    }
    
    return '';
}

// ============================================================================
// GENERATE MESSAGES (Standard)
// ============================================================================


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
    
    const confirmed = confirm('Send all approved messages to LinkedIn? This will send connection requests with personalized messages.');
    if (!confirmed) return;
    
    btn.disabled = true;
    btn.textContent = '⏳ Sending...';
    
    statusDiv.style.display = 'block';
    statusMessage.textContent = '📨 Sending messages to LinkedIn... This may take several minutes.';
    
    try {
        const response = await fetch('/api/linkedin/send-messages', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusMessage.innerHTML = `
                <strong>✅ Sending Complete!</strong><br>
                📨 Sent: ${data.sent}<br>
                ❌ Failed: ${data.failed}<br>
                ⭐ Skipped: ${data.skipped}
            `;
            
            showNotification(`✅ Sent ${data.sent} messages!`, 'success');
            
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
            headers: {'Content-Type': 'application/json'},
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
    alert(message);
}