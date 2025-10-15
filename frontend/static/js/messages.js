/**
 * SC AI Lead Generation System - Messages Page JavaScript
 * ✅ FIXED VERSION with Select All, Auto-Approve, and Hide Variants
 */

// Global state
let currentFilter = 'draft';
let selectedMessages = new Set();

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    loadMessages(currentFilter);
    loadMessageStats();
    setupEventListeners();
    setupSelectAll();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadMessages(currentFilter);
        loadMessageStats();
    }, 30000);
});

/**
 * ✅ NEW: Setup Select All functionality
 */
function setupSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all-messages');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.message-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                const messageId = parseInt(checkbox.dataset.messageId);
                if (this.checked) {
                    selectedMessages.add(messageId);
                } else {
                    selectedMessages.delete(messageId);
                }
            });
            updateBulkActionButtons();
        });
    }
    
    // Setup Auto-Approve All button
    const autoApproveBtn = document.getElementById('auto-approve-all-btn');
    if (autoApproveBtn) {
        autoApproveBtn.addEventListener('click', autoApproveAll);
    }
    
    // Setup Bulk Approve button
    const bulkApproveBtn = document.getElementById('bulk-approve-btn');
    if (bulkApproveBtn) {
        bulkApproveBtn.addEventListener('click', bulkApproveMessages);
    }
    
    // Setup Bulk Delete button
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', bulkDeleteMessages);
    }
}

/**
 * ✅ NEW: Setup individual message checkboxes
 */
function setupMessageCheckboxes() {
    document.querySelectorAll('.message-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const messageId = parseInt(this.dataset.messageId);
            if (this.checked) {
                selectedMessages.add(messageId);
            } else {
                selectedMessages.delete(messageId);
            }
            updateSelectAllCheckbox();
            updateBulkActionButtons();
        });
    });
}

/**
 * ✅ NEW: Update Select All checkbox state
 */
function updateSelectAllCheckbox() {
    const selectAll = document.getElementById('select-all-messages');
    const checkboxes = document.querySelectorAll('.message-checkbox');
    if (selectAll && checkboxes.length > 0) {
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        const someChecked = Array.from(checkboxes).some(cb => cb.checked);
        selectAll.checked = allChecked;
        selectAll.indeterminate = someChecked && !allChecked;
    }
}

/**
 * ✅ NEW: Enable/disable bulk action buttons
 */
function updateBulkActionButtons() {
    const bulkApproveBtn = document.getElementById('bulk-approve-btn');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    
    if (bulkApproveBtn) {
        bulkApproveBtn.disabled = selectedMessages.size === 0;
    }
    if (bulkDeleteBtn) {
        bulkDeleteBtn.disabled = selectedMessages.size === 0;
    }
}

/**
 * ✅ NEW: Auto-approve all drafts (picks Variant A for each lead)
 */
async function autoApproveAll() {
    const draftMessages = document.querySelectorAll('[data-status="draft"]');
    
    if (draftMessages.length === 0) {
        showNotification('No draft messages to approve', 'warning');
        return;
    }
    
    // Group by lead - only approve best variant (Variant A by default)
    const leadVariants = new Map();
    
    draftMessages.forEach(card => {
        const leadId = card.dataset.leadId;
        const variant = card.dataset.variant;
        const messageId = parseInt(card.dataset.messageId);
        
        if (!leadVariants.has(leadId)) {
            leadVariants.set(leadId, []);
        }
        leadVariants.get(leadId).push({ messageId, variant, card });
    });
    
    let successCount = 0;
    
    // For each lead, approve Variant A (or first available)
    for (const [leadId, variants] of leadVariants) {
        // Find Variant A, or take first variant
        const bestVariant = variants.find(v => v.variant === 'A') || variants[0];
        
        try {
            const response = await fetch(`/api/messages/${bestVariant.messageId}/approve`, {
                method: 'POST'
            });
            
            if (response.ok) {
                successCount++;
                hideOtherVariants(leadId, bestVariant.messageId);
            }
        } catch (error) {
            console.error(`Error auto-approving message ${bestVariant.messageId}:`, error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    showNotification(`✅ Auto-approved ${successCount} messages!`, 'success');
    
    // Switch to approved tab
    setTimeout(() => {
        const approvedBtn = document.querySelector('[data-filter="approved"]');
        if (approvedBtn) approvedBtn.click();
    }, 1000);
}

/**
 * ✅ NEW: Bulk approve selected messages
 */
async function bulkApproveMessages() {
    if (selectedMessages.size === 0) {
        showNotification('No messages selected', 'warning');
        return;
    }
    
    const confirmMessage = `Approve ${selectedMessages.size} message(s)?`;
    if (!confirm(confirmMessage)) return;
    
    let successCount = 0;
    let errorCount = 0;
    
    // Group messages by lead to only keep one per lead
    const leadMessages = new Map();
    
    for (const messageId of selectedMessages) {
        const messageCard = document.querySelector(`[data-message-id="${messageId}"]`);
        if (messageCard) {
            const leadId = messageCard.dataset.leadId;
            if (!leadMessages.has(leadId)) {
                leadMessages.set(leadId, messageId);
            }
        }
    }
    
    // Approve one message per lead
    for (const [leadId, messageId] of leadMessages) {
        try {
            const response = await fetch(`/api/messages/${messageId}/approve`, {
                method: 'POST'
            });
            
            if (response.ok) {
                successCount++;
                hideOtherVariants(leadId, messageId);
            } else {
                errorCount++;
            }
        } catch (error) {
            console.error(`Error approving message ${messageId}:`, error);
            errorCount++;
        }
        
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    showNotification(`Approved ${successCount} message(s)`, 'success');
    
    if (errorCount > 0) {
        showNotification(`${errorCount} failed`, 'error');
    }
    
    // Reload and clear selection
    selectedMessages.clear();
    loadMessages(currentFilter);
}

/**
 * ✅ NEW: Bulk delete selected messages
 */
async function bulkDeleteMessages() {
    if (selectedMessages.size === 0) {
        showNotification('No messages selected', 'warning');
        return;
    }
    
    if (!confirm(`Delete ${selectedMessages.size} message(s)?`)) return;
    
    let successCount = 0;
    
    for (const messageId of selectedMessages) {
        try {
            const response = await fetch(`/api/messages/${messageId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                successCount++;
            }
        } catch (error) {
            console.error(`Error deleting message ${messageId}:`, error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    showNotification(`Deleted ${successCount} message(s)`, 'success');
    
    selectedMessages.clear();
    loadMessages(currentFilter);
}

/**
 * ✅ NEW: Hide other variants after approving one
 */
function hideOtherVariants(leadId, approvedMessageId) {
    const messageCards = document.querySelectorAll(`[data-lead-id="${leadId}"]`);
    
    messageCards.forEach(card => {
        const cardMessageId = parseInt(card.dataset.messageId);
        
        // Hide variants that aren't the approved one
        if (cardMessageId !== approvedMessageId) {
            card.style.opacity = '0';
            card.style.transition = 'opacity 0.3s ease-out';
            
            setTimeout(() => {
                card.remove();
            }, 300);
        }
    });
}

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
        const scheduleRes = await fetch('/api/messages/schedule-batch', {
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
        
        // ✅ NEW: Setup checkboxes after messages load
        setTimeout(() => {
            setupMessageCheckboxes();
            updateSelectAllCheckbox();
        }, 100);
        
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
                icon: 'edit'
            },
            'approved': {
                title: 'No Approved Messages',
                desc: 'Approve draft messages to queue them for sending',
                icon: 'check-circle'
            },
            'sent': {
                title: 'No Sent Messages',
                desc: 'Send approved messages to see them here',
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
            <div class="message-card bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6 animate-slide-in"
                 data-lead-id="${leadId}"
                 data-status="${firstStatus}">
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
                <div class="variant-card border-l-4 ${variantColor} bg-gray-50 p-4 rounded relative"
                     data-message-id="${msg.id}"
                     data-lead-id="${leadId}"
                     data-variant="${msg.variant}"
                     data-status="${msg.status}">
                    
                    ${status === 'draft' ? `
                        <input type="checkbox" 
                               class="message-checkbox absolute top-4 left-4" 
                               data-message-id="${msg.id}"
                               style="width: 18px; height: 18px; cursor: pointer;">
                    ` : ''}
                    
                    <div class="flex justify-between items-start mb-2" style="margin-left: ${status === 'draft' ? '35px' : '0'};">
                        <span class="font-semibold text-gray-700">Variant ${msg.variant}</span>
                        <div class="flex space-x-2">
                            ${msg.status === 'draft' ? `
                                <button onclick="approveMessage(${msg.id}, ${leadId})" 
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
                    <p class="text-gray-700 leading-relaxed whitespace-pre-wrap" style="margin-left: ${status === 'draft' ? '35px' : '0'};">${msg.content}</p>
                    <div class="text-xs text-gray-500 mt-2" style="margin-left: ${status === 'draft' ? '35px' : '0'};">
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
        const scheduleRes = await fetch('/api/messages/schedule-batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_ids: data.messages.map(m => m.id),
                start_time: null,
                spread_hours: 1
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
 * ✅ UPDATED: Approve a single message and hide other variants
 */
async function approveMessage(messageId, leadId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message approved!', 'success');
            
            // ✅ FIX: Hide all other variants for this lead
            hideOtherVariants(leadId, messageId);
            
            // Reload messages
            setTimeout(() => {
                loadMessages(currentFilter);
                loadMessageStats();
            }, 500);
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
        type === 'warning' ? 'bg-yellow-500' :
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