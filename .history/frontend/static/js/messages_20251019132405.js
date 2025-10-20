// ============================================================================
// ENHANCED MESSAGE MANAGEMENT - Production Ready
// Features:
// 1. Auto-delete variants when one is approved
// 2. Edit modal before approving
// 3. Lead context cards
// 4. Bulk approve/send workflow
// 5. Message preview
// ============================================================================

let linkedInLoggedIn = false;
let openAIConnected = false;
let currentMessages = [];
let selectedMessageIds = new Set();

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Messages page loaded');
    
    // Check connection status
    checkLinkedInStatus();
    checkOpenAIConnection();
    
    // Load data
    loadMessages();
    loadMessageStats();
    loadTemplates();
    
    // Setup event listeners
    setupEventListeners();
    
    // Refresh every 30 seconds
    setInterval(() => {
        checkLinkedInStatus();
        checkOpenAIConnection();
    }, 30000);
});

function setupEventListeners() {
    // Generate messages button
    const generateBtn = document.getElementById('generate-messages-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateMessages);
    }
    
    // Send approved messages button
    const sendBtn = document.getElementById('send-approved-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendApprovedMessages);
    }
    
    // Save template button
    const saveTemplateBtn = document.getElementById('save-template-btn');
    if (saveTemplateBtn) {
        saveTemplateBtn.addEventListener('click', saveTemplate);
    }
    
    // Apply filter button
    const applyFilterBtn = document.getElementById('apply-filter-btn');
    if (applyFilterBtn) {
        applyFilterBtn.addEventListener('click', applyFilter);
    }
    
    // Bulk actions
    document.getElementById('bulk-approve-btn')?.addEventListener('click', bulkApprove);
    document.getElementById('bulk-reject-btn')?.addEventListener('click', bulkReject);
}

// ============================================================================
// CONNECTION STATUS
// ============================================================================

async function checkLinkedInStatus() {
    try {
        const response = await fetch('/api/linkedin/status');
        const data = await response.json();
        linkedInLoggedIn = data.logged_in || false;
        updateLinkedInStatusUI();
    } catch (error) {
        console.error('Error checking LinkedIn status:', error);
    }
}

async function checkOpenAIConnection() {
    try {
        const response = await fetch('/api/auth/test-connection', {
            method: 'POST'
        });
        const data = await response.json();
        openAIConnected = data.openai_connected || false;
        updateOpenAIStatusUI();
    } catch (error) {
        console.error('Error checking OpenAI connection:', error);
    }
}

function updateLinkedInStatusUI() {
    const statusElement = document.getElementById('linkedin-status');
    if (statusElement) {
        if (linkedInLoggedIn) {
            statusElement.innerHTML = '<i class="fas fa-check-circle"></i> LinkedIn: Connected';
            statusElement.className = 'status-badge status-success';
        } else {
            statusElement.innerHTML = '<i class="fas fa-times-circle"></i> LinkedIn: Not Connected — <a href="/settings">Connect on Dashboard</a>';
            statusElement.className = 'status-badge status-error';
        }
    }
}

function updateOpenAIStatusUI() {
    const statusElement = document.getElementById('openai-status');
    if (statusElement) {
        if (openAIConnected) {
            statusElement.innerHTML = '<i class="fas fa-robot"></i> OpenAI: Connected';
            statusElement.className = 'status-badge status-success';
        } else {
            statusElement.innerHTML = '<i class="fas fa-exclamation-circle"></i> OpenAI: Not Connected';
            statusElement.className = 'status-badge status-warning';
        }
    }
}

// ============================================================================
// LOAD MESSAGES WITH ENHANCED UI
// ============================================================================

async function loadMessages() {
    try {
        const statusFilter = document.getElementById('status-filter')?.value || '';
        
        const response = await fetch(`/api/messages${statusFilter ? '?status=' + statusFilter : ''}`);
        const data = await response.json();
        
        if (data.success) {
            currentMessages = data.messages || [];
            renderMessages(currentMessages);
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messages-container');
    if (!container) return;
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox" style="font-size: 48px; color: #ccc; margin-bottom: 20px;"></i>
                <p>No messages yet. Generate messages for your approved leads!</p>
            </div>
        `;
        return;
    }
    
    // Group messages by lead
    const groupedMessages = groupMessagesByLead(messages);
    
    container.innerHTML = '';
    
    Object.entries(groupedMessages).forEach(([leadName, leadMessages]) => {
        const leadCard = createLeadMessageCard(leadName, leadMessages);
        container.appendChild(leadCard);
    });
}

function groupMessagesByLead(messages) {
    const grouped = {};
    
    messages.forEach(msg => {
        const leadKey = msg.lead_name || 'Unknown Lead';
        if (!grouped[leadKey]) {
            grouped[leadKey] = [];
        }
        grouped[leadKey].push(msg);
    });
    
    return grouped;
}

function createLeadMessageCard(leadName, messages) {
    const card = document.createElement('div');
    card.className = 'lead-message-group';
    
    // Get lead info from first message
    const firstMsg = messages[0];
    const leadInfo = {
        name: firstMsg.lead_name || leadName,
        title: firstMsg.lead_title || 'N/A',
        company: firstMsg.lead_company || 'N/A',
        linkedin_url: firstMsg.linkedin_url || '#'
    };
    
    card.innerHTML = `
        <div class="lead-info-header">
            <div class="lead-avatar">
                ${getInitials(leadInfo.name)}
            </div>
            <div class="lead-details">
                <h3>${leadInfo.name} • ${messages[0].variant || ''}</h3>
                <p class="lead-title">${leadInfo.title} at ${leadInfo.company}</p>
                <a href="${leadInfo.linkedin_url}" target="_blank" class="linkedin-link">
                    <i class="fab fa-linkedin"></i> View Profile
                </a>
            </div>
            <div class="message-actions-top">
                <span class="badge badge-${getStatusColor(messages[0].status)}">${messages[0].status}</span>
                ${messages.length > 1 ? `<span class="variant-count">${messages.length} variants</span>` : ''}
            </div>
        </div>
        
        <div class="message-variants">
            ${messages.map(msg => createMessageVariantHTML(msg)).join('')}
        </div>
    `;
    
    return card;
}

function createMessageVariantHTML(message) {
    const isApproved = message.status === 'approved';
    const isDraft = message.status === 'draft';
    
    return `
        <div class="message-card ${isApproved ? 'approved' : ''}" data-message-id="${message.id}">
            <div class="message-header">
                <div class="message-variant-badge">
                    <span class="variant-label">Variant ${message.variant || 'A'}</span>
                    ${isApproved ? '<i class="fas fa-check-circle" style="color: #10b981;"></i>' : ''}
                </div>
                <div class="message-meta">
                    <small>Created ${formatDate(message.created_at)}</small>
                </div>
            </div>
            
            <div class="message-content">
                <p>${message.content}</p>
                <div class="message-stats">
                    <span class="char-count">${message.content.length}/300 chars</span>
                </div>
            </div>
            
            <div class="message-actions">
                ${isDraft ? `
                    <button class="btn btn-sm btn-secondary" onclick="editMessage(${message.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-success" onclick="approveMessageWithEdit(${message.id})">
                        <i class="fas fa-check"></i> Approve
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="rejectMessage(${message.id})">
                        <i class="fas fa-times"></i> Delete
                    </button>
                ` : ''}
                
                ${isApproved ? `
                    <button class="btn btn-sm btn-primary" onclick="sendSingleMessage(${message.id})">
                        <i class="fas fa-paper-plane"></i> Send Now
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="backToDraft(${message.id})">
                        <i class="fas fa-undo"></i> Back to Draft
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

function getInitials(name) {
    if (!name) return 'NA';
    const parts = name.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function getStatusColor(status) {
    const colors = {
        'draft': 'warning',
        'approved': 'success',
        'sent': 'info',
        'failed': 'danger'
    };
    return colors[status] || 'secondary';
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

// ============================================================================
// APPROVE WITH AUTO-DELETE OTHER VARIANTS + EDIT MODAL
// ============================================================================

async function approveMessageWithEdit(messageId) {
    const message = currentMessages.find(m => m.id === messageId);
    if (!message) return;
    
    // Show edit modal
    const confirmed = await showEditModal(message);
    if (!confirmed) return;
    
    try {
        // Step 1: Approve this message
        const approveResponse = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST'
        });
        
        if (!approveResponse.ok) {
            throw new Error('Failed to approve message');
        }
        
        // Step 2: Delete other variants for same lead
        await deleteOtherVariants(message.lead_id, messageId);
        
        showNotification('✅ Message approved! Other variants deleted.', 'success');
        loadMessages();
        loadMessageStats();
        
    } catch (error) {
        console.error('Error approving message:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    }
}

async function deleteOtherVariants(leadId, approvedMessageId) {
    // Find all messages for this lead
    const leadMessages = currentMessages.filter(m => 
        m.lead_id === leadId && m.id !== approvedMessageId
    );
    
    // Delete each one
    for (const msg of leadMessages) {
        try {
            await fetch(`/api/messages/${msg.id}`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error(`Error deleting message ${msg.id}:`, error);
        }
    }
}

function showEditModal(message) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h3>✏️ Edit Message Before Approving</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Message for ${message.lead_name}</label>
                        <textarea id="edit-message-content" class="form-control" rows="5" maxlength="300">${message.content}</textarea>
                        <small class="char-counter"><span id="char-count">${message.content.length}</span>/300 characters</small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove(); window.editModalResolve(false);">
                        Cancel
                    </button>
                    <button class="btn btn-success" onclick="window.saveAndApprove();">
                        <i class="fas fa-check"></i> Save & Approve
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Character counter
        const textarea = modal.querySelector('#edit-message-content');
        const charCount = modal.querySelector('#char-count');
        textarea.addEventListener('input', () => {
            charCount.textContent = textarea.value.length;
        });
        
        // Global handlers
        window.editModalResolve = resolve;
        window.saveAndApprove = async () => {
            const newContent = textarea.value.trim();
            if (newContent.length === 0) {
                alert('Message cannot be empty');
                return;
            }
            
            // Update message content
            message.content = newContent;
            
            // Save to backend
            await fetch(`/api/messages/${message.id}/update`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: newContent})
            });
            
            modal.remove();
            resolve(true);
        };
    });
}

// ============================================================================
// EDIT MESSAGE
// ============================================================================

async function editMessage(messageId) {
    const message = currentMessages.find(m => m.id === messageId);
    if (!message) return;
    
    const confirmed = await showEditModal(message);
    if (confirmed) {
        showNotification('✅ Message updated', 'success');
        loadMessages();
    }
}

// ============================================================================
// REJECT/DELETE MESSAGE
// ============================================================================

async function rejectMessage(messageId) {
    if (!confirm('Delete this message?')) return;
    
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
            throw new Error(data.error || 'Failed to delete');
        }
    } catch (error) {
        console.error('Error deleting message:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    }
}

// ============================================================================
// BACK TO DRAFT
// ============================================================================

async function backToDraft(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'draft'})
        });
        
        if (response.ok) {
            showNotification('✅ Moved back to draft', 'success');
            loadMessages();
            loadMessageStats();
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error updating status', 'error');
    }
}

// ============================================================================
// SEND SINGLE MESSAGE
// ============================================================================

async function sendSingleMessage(messageId) {
    if (!linkedInLoggedIn) {
        showNotification('❌ Please connect LinkedIn first', 'error');
        return;
    }
    
    if (!confirm('Send this message now?')) return;
    
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
            throw new Error(data.error || 'Failed to send');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    }
}

// ============================================================================
// GENERATE MESSAGES (UPDATED)
// ============================================================================

async function generateMessages() {
    const btn = document.getElementById('generate-messages-btn');
    const statusDiv = document.getElementById('action-status');
    const statusMessage = document.getElementById('action-message');
    
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    
    statusDiv.style.display = 'block';
    statusMessage.textContent = 'Fetching qualified leads...';
    
    try {
        // STEP 1: Fetch qualified leads
        console.log('🎯 Fetching qualified leads...');
        const leadsResponse = await fetch('/api/leads/top?min_score=70&limit=10');
        const leadsData = await leadsResponse.json();
        
        console.log('📊 Leads response:', leadsData);
        
        if (!leadsData.success || !leadsData.leads || leadsData.leads.length === 0) {
            throw new Error('No qualified leads found. Please approve some leads first (score >= 70).');
        }
        
        const leadIds = leadsData.leads.map(lead => lead.id);
        console.log(`✅ Found ${leadIds.length} qualified leads:`, leadIds);
        
        statusMessage.textContent = `Generating A/B/C message variants for ${leadIds.length} leads... This may take a minute.`;
        
        // STEP 2: Generate messages
        console.log('🎨 Generating messages for leads:', leadIds);
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                lead_ids: leadIds
            })
        });
        
        const data = await response.json();
        console.log('📨 Generation response:', data);
        
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
        console.error('❌ Error generating messages:', error);
        statusMessage.textContent = '❌ Error: ' + error.message;
        showNotification('❌ Generation failed: ' + error.message, 'error');
        
    } finally {
        btn.disabled = false;
        btn.textContent = '🎨 Generate Messages for Top Leads';
    }
}

// ============================================================================
// SEND APPROVED MESSAGES
// ============================================================================

async function sendApprovedMessages() {
    if (!linkedInLoggedIn) {
        showNotification('❌ Please connect LinkedIn on the Dashboard first', 'error');
        return;
    }
    
    const approvedMessages = currentMessages.filter(m => m.status === 'approved');
    
    if (approvedMessages.length === 0) {
        showNotification('❌ No approved messages to send', 'error');
        return;
    }
    
    if (!confirm(`Send ${approvedMessages.length} approved messages?`)) return;
    
    const btn = document.getElementById('send-approved-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Sending...';
    
    try {
        const response = await fetch('/api/messages/send', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✅ Sent ${data.sent} messages${data.failed ? `, ${data.failed} failed` : ''}`, 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.error || 'Failed to send');
        }
    } catch (error) {
        console.error('Error sending messages:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '📤 Send Approved Messages';
    }
}

// ============================================================================
// BULK ACTIONS
// ============================================================================

async function bulkApprove() {
    if (selectedMessageIds.size === 0) {
        showNotification('❌ No messages selected', 'error');
        return;
    }
    
    if (!confirm(`Approve ${selectedMessageIds.size} messages?`)) return;
    
    for (const id of selectedMessageIds) {
        await approveMessageWithEdit(id);
    }
    
    selectedMessageIds.clear();
}

async function bulkReject() {
    if (selectedMessageIds.size === 0) {
        showNotification('❌ No messages selected', 'error');
        return;
    }
    
    if (!confirm(`Delete ${selectedMessageIds.size} messages?`)) return;
    
    for (const id of selectedMessageIds) {
        await rejectMessage(id);
    }
    
    selectedMessageIds.clear();
}

// ============================================================================
// LOAD STATS
// ============================================================================

async function loadMessageStats() {
    try {
        const response = await fetch('/api/messages/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            updateStatsUI(data.stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateStatsUI(stats) {
    document.getElementById('draft-count').textContent = stats.draft || 0;
    document.getElementById('approved-count').textContent = stats.approved || 0;
    document.getElementById('sent-count').textContent = stats.sent || 0;
    
    const replyRate = stats.total > 0 ? ((stats.replied / stats.total) * 100).toFixed(1) : 0;
    document.getElementById('reply-rate').textContent = replyRate + '%';
}

// ============================================================================
// TEMPLATES
// ============================================================================

async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const data = await response.json();
        
        if (data.success) {
            renderTemplates(data.templates || []);
        }
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templates-list');
    if (!container) return;
    
    if (templates.length === 0) {
        container.innerHTML = '<p class="text-muted">No templates saved yet</p>';
        return;
    }
    
    container.innerHTML = templates.map(t => `
        <div class="template-item">
            <div class="template-content">${t.template.substring(0, 100)}...</div>
            <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${t.id})">Delete</button>
        </div>
    `).join('');
}

async function saveTemplate() {
    const textarea = document.getElementById('template-text');
    const template = textarea.value.trim();
    
    if (!template) {
        showNotification('❌ Please enter a template', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/templates/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({template})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Template saved', 'success');
            textarea.value = '';
            loadTemplates();
        }
    } catch (error) {
        console.error('Error saving template:', error);
        showNotification('❌ Error saving template', 'error');
    }
}

async function deleteTemplate(templateId) {
    if (!confirm('Delete this template?')) return;
    
    try {
        const response = await fetch(`/api/templates/${templateId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('✅ Template deleted', 'success');
            loadTemplates();
        }
    } catch (error) {
        console.error('Error deleting template:', error);
    }
}

// ============================================================================
// FILTER
// ============================================================================

function applyFilter() {
    loadMessages();
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}