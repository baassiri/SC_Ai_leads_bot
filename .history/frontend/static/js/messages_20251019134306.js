// ============================================================================
// ENHANCED MESSAGE MANAGEMENT - FINAL FIXED VERSION
// ============================================================================

let linkedInLoggedIn = false;
let openAIConnected = false;
let currentMessages = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('Messages page loaded');
    loadMessages();
    loadMessageStats();
    
    document.getElementById('generate-messages-btn')?.addEventListener('click', generateMessages);
    document.getElementById('send-messages-btn')?.addEventListener('click', sendApprovedMessages);
    document.getElementById('apply-filters-btn')?.addEventListener('click', () => loadMessages());
});

// ============================================================================
// LOAD MESSAGES
// ============================================================================

async function loadMessages() {
    try {
        const statusFilter = document.getElementById('status-filter')?.value || '';
        const response = await fetch(`/api/messages${statusFilter ? '?status=' + statusFilter : ''}`);
        const data = await response.json();
        
        if (data.success) {
            currentMessages = data.messages || [];
            console.log('Loaded messages:', currentMessages);
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
    
    // Group by lead
    const grouped = {};
    messages.forEach(msg => {
        const leadKey = msg.lead_name || 'Unknown';
        if (!grouped[leadKey]) grouped[leadKey] = [];
        grouped[leadKey].push(msg);
    });
    
    container.innerHTML = Object.entries(grouped).map(([leadName, msgs]) => {
        const first = msgs[0];
        return `
            <div class="lead-message-group">
                <div class="lead-info-header">
                    <div class="lead-avatar">${getInitials(leadName)}</div>
                    <div class="lead-details">
                        <h3>${leadName}</h3>
                        <p class="lead-title">${first.lead_title || 'N/A'} at ${first.lead_company || 'N/A'}</p>
                        <a href="${first.linkedin_url || '#'}" target="_blank" class="linkedin-link">
                            <i class="fab fa-linkedin"></i> View Profile
                        </a>
                    </div>
                    <div class="message-actions-top">
                        <span class="badge badge-${getStatusColor(first.status)}">${first.status}</span>
                        ${msgs.length > 1 ? `<span class="variant-count">${msgs.length} variants</span>` : ''}
                    </div>
                </div>
                <div class="message-variants">
                    ${msgs.map(msg => createMessageCard(msg)).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function createMessageCard(msg) {
    const isApproved = msg.status === 'approved';
    const isDraft = msg.status === 'draft';
    
    return `
        <div class="message-card ${isApproved ? 'approved' : ''}" data-message-id="${msg.id}">
            <div class="message-header">
                <div class="message-variant-badge">
                    <span class="variant-label">Variant ${msg.variant || 'A'}</span>
                    ${isApproved ? '<i class="fas fa-check-circle" style="color: #10b981;"></i>' : ''}
                </div>
                <div class="message-meta">
                    <small>Created ${formatDate(msg.created_at)}</small>
                </div>
            </div>
            <div class="message-content">
                <p>${msg.content}</p>
                <div class="message-stats">
                    <span class="char-count">${msg.content.length}/300 chars</span>
                </div>
            </div>
            <div class="message-actions">
                ${isDraft ? `
                    <button class="btn btn-sm btn-success" onclick="approveMessage(${msg.id}, ${msg.lead_id})">
                        <i class="fas fa-check"></i> Approve
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteMessage(${msg.id})">
                        <i class="fas fa-times"></i> Delete
                    </button>
                ` : ''}
                ${isApproved ? `
                    <button class="btn btn-sm btn-primary" onclick="sendSingleMessage(${msg.id})">
                        <i class="fas fa-paper-plane"></i> Send Now
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="backToDraft(${msg.id})">
                        <i class="fas fa-undo"></i> Back to Draft
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

// ============================================================================
// APPROVE MESSAGE - AUTO DELETE VARIANTS
// ============================================================================

async function approveMessage(messageId, leadId) {
    console.log('Approving message:', messageId, 'for lead:', leadId);
    
    if (!confirm('Approve this message? Other variants will be deleted.')) return;
    
    try {
        // Step 1: Approve
        const response = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to approve');
        
        // Step 2: Delete other variants
        const otherMessages = currentMessages.filter(m => 
            m.lead_id === leadId && m.id !== messageId
        );
        
        console.log('Deleting', otherMessages.length, 'other variants');
        
        for (const msg of otherMessages) {
            await fetch(`/api/messages/${msg.id}`, { method: 'DELETE' });
        }
        
        showNotification('✅ Message approved! Other variants deleted.', 'success');
        loadMessages();
        loadMessageStats();
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    }
}

async function deleteMessage(messageId) {
    if (!confirm('Delete this message?')) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message deleted', 'success');
            loadMessages();
            loadMessageStats();
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error deleting message', 'error');
    }
}

async function backToDraft(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'draft'})
        });
        
        if (response.ok) {
            showNotification('✅ Moved to draft', 'success');
            loadMessages();
            loadMessageStats();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function sendSingleMessage(messageId) {
    if (!confirm('Send this message now?')) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}/send`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message sent!', 'success');
            loadMessages();
            loadMessageStats();
        } else {
            throw new Error(data.error || 'Failed to send');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error: ' + error.message, 'error');
    }
}

// ============================================================================
// GENERATE & SEND
// ============================================================================

async function generateMessages() {
    const btn = document.getElementById('generate-messages-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    
    try {
        const leadsResponse = await fetch('/api/leads/top?min_score=70&limit=10');
        const leadsData = await leadsResponse.json();
        
        if (!leadsData.success || !leadsData.leads || leadsData.leads.length === 0) {
            throw new Error('No qualified leads found');
        }
        
        const leadIds = leadsData.leads.map(lead => lead.id);
        
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lead_ids: leadIds})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ ' + data.message, 'success');
            setTimeout(() => {
                loadMessages();
                loadMessageStats();
            }, 1000);
        } else {
            throw new Error(data.error || 'Generation failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🎨 Generate Messages for Top Leads';
    }
}

async function sendApprovedMessages() {
    const approved = currentMessages.filter(m => m.status === 'approved');
    if (approved.length === 0) {
        showNotification('❌ No approved messages', 'error');
        return;
    }
    
    if (!confirm(`Send ${approved.length} messages?`)) return;
    
    try {
        const response = await fetch('/api/messages/send', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✅ Sent ${data.sent} messages`, 'success');
            loadMessages();
            loadMessageStats();
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('❌ Error sending messages', 'error');
    }
}

// ============================================================================
// STATS
// ============================================================================

async function loadMessageStats() {
    try {
        const response = await fetch('/api/messages/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            document.getElementById('draft-count').textContent = data.stats.draft || 0;
            document.getElementById('approved-count').textContent = data.stats.approved || 0;
            document.getElementById('sent-count').textContent = data.stats.sent || 0;
            const replyRate = data.stats.total > 0 ? ((data.stats.replied / data.stats.total) * 100).toFixed(1) : 0;
            document.getElementById('reply-rate').textContent = replyRate + '%';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ============================================================================
// TEMPLATES
// ============================================================================

async function saveTemplate() {
    const textarea = document.getElementById('templateText');
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
        console.error('Error:', error);
        showNotification('❌ Error saving template', 'error');
    }
}

async function loadTemplates() {
    try {
        const response = await fetch('/api/templates');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('savedTemplates');
            if (data.templates && data.templates.length > 0) {
                container.style.display = 'block';
                container.innerHTML = data.templates.map(t => `
                    <div class="template-item">
                        <p>${t.template.substring(0, 100)}...</p>
                        <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${t.id})">Delete</button>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function deleteTemplate(templateId) {
    if (!confirm('Delete template?')) return;
    
    try {
        await fetch(`/api/templates/${templateId}`, { method: 'DELETE' });
        showNotification('✅ Template deleted', 'success');
        loadTemplates();
    } catch (error) {
        console.error('Error:', error);
    }
}

// ============================================================================
// HELPERS
// ============================================================================

function getInitials(name) {
    if (!name) return 'NA';
    const parts = name.split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
}

function getStatusColor(status) {
    const colors = { draft: 'warning', approved: 'success', sent: 'info', failed: 'danger' };
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
    setTimeout(() => notification.remove(), 3000);
}