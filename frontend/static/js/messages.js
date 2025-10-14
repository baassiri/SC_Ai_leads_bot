/**
 * SC AI Lead Generation System - Messages Page JavaScript
 * Handles message generation, approval, scheduling, and SENDING
 */

// Global state
let currentFilter = 'draft';

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    loadMessages(currentFilter);
    loadMessageStats();
    setupEventListeners();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadMessages(currentFilter);
        loadMessageStats();
    }, 30000);
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Filter buttons
    const filterBtns = document.querySelectorAll('[data-filter]');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            currentFilter = this.dataset.filter;
            loadMessages(currentFilter);
            
            // Update active state
            filterBtns.forEach(b => {
                b.classList.remove('ring-2', 'ring-blue-500');
            });
            this.classList.add('ring-2', 'ring-blue-500');
        });
    });
}

/**
 * Approve all draft messages
 */
async function approveAllDrafts() {
    if (!confirm('Approve all draft messages?')) return;
    
    try {
        const response = await fetch('/api/messages?status=draft');
        const data = await response.json();
        
        if (!data.success || !data.messages.length) {
            alert('No draft messages found');
            return;
        }
        
        let approved = 0;
        for (const msg of data.messages) {
            const approveRes = await fetch(`/api/messages/${msg.id}/approve`, {
                method: 'POST'
            });
            const approveData = await approveRes.json();
            if (approveData.success) approved++;
        }
        
        alert(`✅ Approved ${approved} messages!`);
        loadMessages(currentFilter);
        loadMessageStats();
        
    } catch (error) {
        alert('Error approving messages');
        console.error(error);
    }
}

/**
 * Send all approved messages
 */
async function sendAllApprovedMessages() {
    if (!confirm('Send all approved messages now? This will schedule them with rate limiting.')) return;
    
    try {
        const response = await fetch('/api/messages?status=approved');
        const data = await response.json();
        
        if (!data.success || !data.messages.length) {
            alert('No approved messages found');
            return;
        }
        
        // Schedule all approved messages
        const scheduleRes = await fetch('/api/schedule/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_ids: data.messages.map(m => m.id),
                start_time: null, // ASAP
                spread_hours: 4
            })
        });
        
        const scheduleData = await scheduleRes.json();
        
        if (scheduleData.success) {
            alert(`✅ Scheduled ${data.messages.length} messages for sending!`);
            loadMessages(currentFilter);
            loadMessageStats();
        } else {
            alert('Error: ' + scheduleData.message);
        }
        
    } catch (error) {
        alert('Error sending messages');
        console.error(error);
    }
}

/**
 * Send a single message
 */
async function sendMessage(messageId) {
    if (!confirm('Send this message now?')) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}/send`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Message queued for sending!');
            loadMessages(currentFilter);
            loadMessageStats();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error sending message');
        console.error(error);
    }
}

/**
 * Load messages from API
 */
async function loadMessages(status = 'draft') {
    const container = document.getElementById('messages-container');
    
    container.innerHTML = `
        <div class="bg-white rounded-lg shadow p-8 text-center">
            <i data-feather="loader" class="w-12 h-12 mx-auto animate-spin text-blue-500 mb-4"></i>
            <p class="text-gray-500">Loading messages...</p>
        </div>
    `;
    feather.replace();
    
    try {
        const response = await fetch(`/api/messages?status=${status}`);
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.message || 'Failed to load messages');
        }
        
        displayMessages(data.messages, status);
        
    } catch (error) {
        console.error('Error loading messages:', error);
        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <i data-feather="alert-circle" class="w-12 h-12 mx-auto text-red-500 mb-4"></i>
                <p class="text-red-700">Error loading messages: ${error.message}</p>
            </div>
        `;
        feather.replace();
    }
}

/**
 * Display messages grouped by lead
 */
function displayMessages(messages, status) {
    const container = document.getElementById('messages-container');
    
    if (!messages || messages.length === 0) {
        const emptyMessages = {
            'draft': {
                title: 'No Draft Messages',
                desc: 'Generate A/B/C message variants to get started',
                action: 'Generate Messages',
                icon: 'edit'
            },
            'approved': {
                title: 'No Approved Messages',
                desc: 'Approve draft messages to queue them for sending',
                action: 'View Drafts',
                icon: 'check-circle'
            },
            'sent': {
                title: 'No Sent Messages',
                desc: 'Send approved messages to see them here',
                action: 'View Approved',
                icon: 'send'
            }
        };
        
        const empty = emptyMessages[status] || emptyMessages.draft;
        
        container.innerHTML = `
            <div class="text-center py-12">
                <i data-feather="${empty.icon}" class="w-16 h-16 mx-auto text-gray-400 mb-4"></i>
                <h3 class="text-xl font-semibold text-gray-700 mb-2">${empty.title}</h3>
                <p class="text-gray-500 mb-6">${empty.desc}</p>
            </div>
        `;
        feather.replace();
        return;
    }
    
    // Group messages by lead
    const messagesByLead = {};
    messages.forEach(msg => {
        if (!messagesByLead[msg.lead_id]) {
            messagesByLead[msg.lead_id] = {
                lead_name: msg.lead_name,
                lead_title: msg.lead_title || 'Unknown Title',
                lead_company: msg.lead_company || 'Unknown Company',
                variants: []
            };
        }
        messagesByLead[msg.lead_id].variants.push(msg);
    });
    
    // Build HTML
    let html = '';
    
    for (const [leadId, data] of Object.entries(messagesByLead)) {
        // Sort variants A, B, C
        data.variants.sort((a, b) => a.variant.localeCompare(b.variant));
        
        const firstStatus = data.variants[0].status;
        
        html += `
            <div class="message-card bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 animate-slide-in">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">${data.lead_name}</h3>
                        <p class="text-sm text-gray-600">${data.lead_title} at ${data.lead_company}</p>
                    </div>
                    <div class="flex items-center space-x-2">
                        ${getStatusBadge(firstStatus)}
                        ${firstStatus === 'approved' ? `
                            <button onclick="sendAllVariantsForLead(${leadId})" 
                                    class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm flex items-center">
                                <i data-feather="send" class="w-4 h-4 mr-1"></i> Send All
                            </button>
                        ` : ''}
                    </div>
                </div>
                
                <div class="space-y-4">
        `;
        
        // Display each variant
        data.variants.forEach(msg => {
            const variantColor = getVariantColor(msg.variant);
            
            html += `
                <div class="variant-card border-l-4 ${variantColor} bg-gray-50 p-4 rounded">
                    <div class="flex justify-between items-start mb-2">
                        <span class="font-semibold text-gray-700">Variant ${msg.variant}</span>
                        <div class="flex space-x-2">
                            ${msg.status === 'draft' ? `
                                <button onclick="approveMessage(${msg.id})" 
                                        class="text-green-600 hover:text-green-700"
                                        title="Approve">
                                    <i data-feather="check-circle" class="w-5 h-5"></i>
                                </button>
                                <button onclick="editMessage(${msg.id})" 
                                        class="text-blue-600 hover:text-blue-700"
                                        title="Edit">
                                    <i data-feather="edit-2" class="w-5 h-5"></i>
                                </button>
                                <button onclick="deleteMessage(${msg.id})" 
                                        class="text-red-600 hover:text-red-700"
                                        title="Delete">
                                    <i data-feather="trash-2" class="w-5 h-5"></i>
                                </button>
                            ` : msg.status === 'approved' ? `
                                <button onclick="sendMessage(${msg.id})" 
                                        class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm flex items-center"
                                        title="Send Now">
                                    <i data-feather="send" class="w-4 h-4 mr-1"></i> Send
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    <p class="text-gray-700 leading-relaxed whitespace-pre-wrap">${msg.content}</p>
                    <div class="text-xs text-gray-500 mt-2">
                        ${msg.content.length} characters
                        ${msg.sent_at ? ` • Sent ${getTimeAgo(msg.sent_at)}` : ''}
                        ${msg.scheduled_time ? ` • Scheduled for ${new Date(msg.scheduled_time).toLocaleString()}` : ''}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    feather.replace();
}

/**
 * Send all variants for a specific lead
 */
async function sendAllVariantsForLead(leadId) {
    if (!confirm('Send all 3 message variants for this lead?')) return;
    
    try {
        const response = await fetch(`/api/messages?lead_id=${leadId}&status=approved`);
        const data = await response.json();
        
        if (!data.success || !data.messages.length) {
            alert('No approved messages found for this lead');
            return;
        }
        
        // Schedule all variants
        const scheduleRes = await fetch('/api/schedule/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_ids: data.messages.map(m => m.id),
                start_time: null,
                spread_hours: 1 // Spread over 1 hour
            })
        });
        
        const scheduleData = await scheduleRes.json();
        
        if (scheduleData.success) {
            alert(`✅ Scheduled ${data.messages.length} variants for sending!`);
            loadMessages(currentFilter);
        } else {
            alert('Error: ' + scheduleData.message);
        }
        
    } catch (error) {
        alert('Error sending messages');
        console.error(error);
    }
}

/**
 * Approve a single message
 */
async function approveMessage(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message approved!', 'success');
            loadMessages(currentFilter);
            loadMessageStats();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error approving message');
        console.error(error);
    }
}

/**
 * Delete a message
 */
async function deleteMessage(messageId) {
    if (!confirm('Delete this message?')) return;
    
    try {
        const response = await fetch(`/api/messages/${messageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message deleted', 'success');
            loadMessages(currentFilter);
            loadMessageStats();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        alert('Error deleting message');
        console.error(error);
    }
}

/**
 * Edit message (placeholder)
 */
function editMessage(messageId) {
    alert('Edit functionality coming soon!');
}

/**
 * Get variant border color
 */
function getVariantColor(variant) {
    const colors = {
        'A': 'border-blue-500',
        'B': 'border-green-500',
        'C': 'border-purple-500'
    };
    return colors[variant] || 'border-gray-500';
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
    const badges = {
        'draft': '<span class="px-3 py-1 bg-gray-200 text-gray-700 rounded-full text-sm">Draft</span>',
        'approved': '<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">Approved</span>',
        'sent': '<span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">Sent</span>',
        'scheduled': '<span class="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm">Scheduled</span>',
        'failed': '<span class="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">Failed</span>'
    };
    return badges[status] || badges.draft;
}

/**
 * Load message statistics
 */
async function loadMessageStats() {
    try {
        const response = await fetch('/api/messages/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('stat-draft').textContent = data.stats.draft || 0;
            document.getElementById('stat-approved').textContent = data.stats.approved || 0;
            document.getElementById('stat-sent').textContent = data.stats.sent || 0;
            document.getElementById('stat-total').textContent = data.stats.total || 0;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    } z-50 animate-slide-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Get time ago string
 */
function getTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}