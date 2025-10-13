/**
 * SC AI Lead Generation System - Messages Page JavaScript
 * Handles message generation, approval, and scheduling
 */

// Global state
let selectedLeadIds = [];

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    loadMessages();
    loadMessageStats();
    setupEventListeners();
    
    // Auto-refresh every 30 seconds
    setInterval(loadMessageStats, 30000);
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Generate Messages button
    const generateBtn = document.getElementById('generate-messages-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateMessages);
    }
    
    // Approve All button
    const approveAllBtn = document.getElementById('approve-all-btn');
    if (approveAllBtn) {
        approveAllBtn.addEventListener('click', approveAllMessages);
    }
    
    // Filter buttons
    const filterBtns = document.querySelectorAll('[data-filter]');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const status = this.dataset.filter;
            filterMessages(status);
            
            // Update active state
            filterBtns.forEach(b => b.classList.remove('bg-blue-600', 'text-white'));
            filterBtns.forEach(b => b.classList.add('bg-gray-200', 'text-gray-700'));
            this.classList.remove('bg-gray-200', 'text-gray-700');
            this.classList.add('bg-blue-600', 'text-white');
        });
    });
}

/**
 * Generate A/B/C messages for selected leads
 */
async function generateMessages() {
    const btn = document.getElementById('generate-messages-btn');
    
    // Check if leads are selected
    const selectedCheckboxes = document.querySelectorAll('.lead-checkbox:checked');
    const leadIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.dataset.leadId));
    
    // Show confirmation
    let message = leadIds.length > 0 
        ? `Generate A/B/C message variants for ${leadIds.length} selected leads?`
        : 'No leads selected. Generate for top 20 leads (score ≥ 70)?';
    
    if (!confirm(message)) {
        return;
    }
    
    // Disable button and show loading
    btn.disabled = true;
    btn.innerHTML = '<i data-feather="loader" class="w-4 h-4 animate-spin inline"></i> Generating...';
    feather.replace();
    
    try {
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lead_ids: leadIds
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(
                `✅ Generated ${data.results.messages_created} message variants for ${data.results.successful} leads!`,
                'success'
            );
            
            // Reload messages
            setTimeout(() => {
                loadMessages();
                loadMessageStats();
            }, 1000);
        } else {
            showNotification(`❌ Error: ${data.message}`, 'error');
        }
        
    } catch (error) {
        console.error('Error generating messages:', error);
        showNotification('❌ Failed to generate messages. Check console for details.', 'error');
    } finally {
        // Re-enable button
        btn.disabled = false;
        btn.innerHTML = '<i data-feather="message-square" class="w-4 h-4"></i> Generate Messages';
        feather.replace();
    }
}

/**
 * Load messages from API
 */
async function loadMessages(status = null) {
    const container = document.getElementById('messages-container');
    
    if (!container) return;
    
    // Show loading
    container.innerHTML = '<div class="text-center py-8"><i data-feather="loader" class="w-8 h-8 animate-spin mx-auto"></i><p class="mt-2">Loading messages...</p></div>';
    feather.replace();
    
    try {
        const url = status ? `/api/messages?status=${status}` : '/api/messages';
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            displayMessages(data.messages);
        } else {
            container.innerHTML = `<p class="text-red-600">Error: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        container.innerHTML = '<p class="text-red-600">Failed to load messages</p>';
    }
}

/**
 * Display messages in the UI
 */
function displayMessages(messages) {
    const container = document.getElementById('messages-container');
    
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <i data-feather="inbox" class="w-16 h-16 mx-auto text-gray-400 mb-4"></i>
                <h3 class="text-xl font-semibold text-gray-700 mb-2">No Messages Yet</h3>
                <p class="text-gray-500 mb-6">Generate your first A/B/C message variants to get started</p>
                <button onclick="document.getElementById('generate-messages-btn').click()" 
                        class="btn-primary px-6 py-3">
                    <i data-feather="message-square" class="w-5 h-5 inline mr-2"></i>
                    Generate Messages
                </button>
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
                lead_company: msg.lead_company,
                lead_title: msg.lead_title,
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
        
        html += `
            <div class="message-card bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">${data.lead_name}</h3>
                        <p class="text-sm text-gray-600">${data.lead_title} at ${data.lead_company}</p>
                    </div>
                    <div class="flex space-x-2">
                        ${getStatusBadge(data.variants[0].status)}
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
                            ` : ''}
                        </div>
                    </div>
                    <p class="text-gray-700 leading-relaxed">${msg.content}</p>
                    <div class="text-xs text-gray-500 mt-2">
                        ${msg.content.length} characters
                        ${msg.sent_at ? ` • Sent ${getTimeAgo(msg.sent_at)}` : ''}
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
        console.error('Error loading message stats:', error);
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
            loadMessages();
            loadMessageStats();
        } else {
            showNotification(`❌ Error: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error approving message:', error);
        showNotification('❌ Failed to approve message', 'error');
    }
}

/**
 * Approve all draft messages
 */
async function approveAllMessages() {
    if (!confirm('Approve all draft messages?')) {
        return;
    }
    
    // TODO: Implement bulk approve endpoint
    showNotification('⚠️ Bulk approve coming soon!', 'warning');
}

/**
 * Edit message
 */
function editMessage(messageId) {
    // TODO: Implement edit modal
    showNotification('⚠️ Edit feature coming soon!', 'warning');
}

/**
 * Delete message
 */
async function deleteMessage(messageId) {
    if (!confirm('Delete this message?')) {
        return;
    }
    
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
            showNotification(`❌ Error: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error deleting message:', error);
        showNotification('❌ Failed to delete message', 'error');
    }
}

/**
 * Filter messages by status
 */
function filterMessages(status) {
    loadMessages(status === 'all' ? null : status);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Use shared notification system
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        alert(message);
    }
}

/**
 * Get relative time
 */
function getTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        return `${mins}m ago`;
    }
    if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        return `${hours}h ago`;
    }
    const days = Math.floor(seconds / 86400);
    return `${days}d ago`;
}