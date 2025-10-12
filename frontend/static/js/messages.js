/**
 * SC AI Lead Generation System - Enhanced Messages JavaScript
 * Handles message loading, approval, editing, and A/B/C testing
 */

let allMessages = [];
let currentLeadMessages = {};
let currentFilter = 'draft';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMessages('draft');
    loadLeadsForFilter();
    setupFilterButtons();
});

/**
 * Setup filter buttons
 */
function setupFilterButtons() {
    const filterButtons = document.querySelectorAll('[data-filter]');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            currentFilter = filter;
            loadMessages(filter);
            
            // Update active button
            filterButtons.forEach(b => b.classList.remove('ring-2', 'ring-blue-500'));
            this.classList.add('ring-2', 'ring-blue-500');
        });
    });
}

/**
 * Load all messages from API
 */
async function loadMessages(status = 'draft') {
    const container = document.getElementById('messages-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="bg-white rounded-lg shadow p-8 text-center">
            <i data-feather="loader" class="w-12 h-12 mx-auto animate-spin text-blue-500 mb-4"></i>
            <p class="text-gray-500">Loading messages...</p>
        </div>
    `;
    feather.replace();
    
    try {
        const response = await fetch(`/api/messages?status=${status}&limit=200`);
        const data = await response.json();
        
        if (data.success) {
            allMessages = data.messages;
            groupMessagesByLead();
            displayMessages();
        } else {
            showError('Failed to load messages');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        showError('Error loading messages. Please try again.');
    }
}

/**
 * Group messages by lead
 */
function groupMessagesByLead() {
    currentLeadMessages = {};
    
    allMessages.forEach(msg => {
        const leadId = msg.lead_id;
        if (!currentLeadMessages[leadId]) {
            currentLeadMessages[leadId] = {
                lead_name: msg.lead_name || 'Unknown Lead',
                lead_title: msg.lead_title,
                lead_company: msg.lead_company,
                messages: []
            };
        }
        currentLeadMessages[leadId].messages.push(msg);
    });
}

/**
 * Display messages in the UI
 */
function displayMessages() {
    const container = document.getElementById('messages-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    // If no messages
    if (Object.keys(currentLeadMessages).length === 0) {
        container.innerHTML = `
            <div class="bg-white p-8 rounded-lg shadow text-center">
                <i data-feather="message-square" class="w-16 h-16 mx-auto text-gray-400 mb-4"></i>
                <p class="text-gray-500 text-lg mb-2">No ${currentFilter} messages yet</p>
                <p class="text-gray-400 text-sm">Generate messages for your leads to get started</p>
                <button onclick="window.location.href='/leads'" class="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md">
                    Go to Leads
                </button>
            </div>
        `;
        feather.replace();
        return;
    }
    
    // Display each lead's messages
    Object.entries(currentLeadMessages).forEach(([leadId, data]) => {
        const leadCard = createLeadMessageCard(leadId, data);
        container.appendChild(leadCard);
    });
    
    feather.replace();
}

/**
 * Create a card for a lead's messages
 */
function createLeadMessageCard(leadId, data) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-md overflow-hidden mb-6';
    
    const leadName = data.lead_name || 'Unknown Lead';
    const leadTitle = data.lead_title || 'Unknown Title';
    const leadCompany = data.lead_company || 'Unknown Company';
    const messages = data.messages;
    
    // Group by variant
    const variants = { 'A': [], 'B': [], 'C': [] };
    messages.forEach(msg => {
        const variant = msg.variant || 'A';
        if (variants[variant]) {
            variants[variant].push(msg);
        }
    });
    
    card.innerHTML = `
        <div class="bg-gradient-to-r from-blue-500 to-blue-600 p-4 text-white">
            <div class="flex justify-between items-start">
                <div>
                    <h3 class="text-xl font-bold">${leadName}</h3>
                    <p class="text-blue-100 text-sm">${leadTitle} at ${leadCompany}</p>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-3 py-1 bg-white bg-opacity-20 rounded-full text-sm">
                        ${messages.length} message${messages.length !== 1 ? 's' : ''}
                    </span>
                    <a href="/leads" class="text-white hover:text-blue-100" title="View Lead">
                        <i data-feather="external-link" class="w-4 h-4"></i>
                    </a>
                </div>
            </div>
        </div>
        
        <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                ${Object.entries(variants).map(([variant, msgs]) => 
                    msgs.length > 0 ? createVariantCard(variant, msgs[0]) : ''
                ).join('')}
            </div>
        </div>
    `;
    
    return card;
}

/**
 * Create a variant card (A, B, or C)
 */
function createVariantCard(variant, msg) {
    const isApproved = msg.status === 'approved';
    const isSent = msg.status === 'sent';
    const isDraft = msg.status === 'draft';
    
    const variantColors = {
        'A': { bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800' },
        'B': { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-800' },
        'C': { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800' }
    };
    
    const colors = variantColors[variant] || variantColors['A'];
    
    return `
        <div class="border-2 ${colors.border} ${colors.bg} rounded-lg p-4 transition-all hover:shadow-md">
            <div class="flex justify-between items-start mb-3">
                <div class="flex items-center space-x-2">
                    <span class="font-bold text-lg ${colors.badge} px-3 py-1 rounded-md">
                        Variant ${variant}
                    </span>
                    ${isSent ? `<span class="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Sent</span>` : ''}
                    ${isApproved && !isSent ? `<span class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">Approved</span>` : ''}
                    ${isDraft ? `<span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">Draft</span>` : ''}
                </div>
                <span class="text-xs text-gray-500">${msg.content.length} chars</span>
            </div>
            
            <div class="bg-white rounded-lg p-3 mb-3 text-gray-700 min-h-[100px] border border-gray-200" id="message-content-${msg.id}">
                ${msg.content}
            </div>
            
            <div class="flex flex-wrap items-center gap-2">
                ${!isSent ? `
                    ${isDraft ? `
                        <button onclick="approveMessage(${msg.id})" class="text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded-md flex items-center transition">
                            <i data-feather="check" class="w-3 h-3 mr-1"></i> Approve
                        </button>
                        <button onclick="editMessage(${msg.id})" class="text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-md flex items-center transition">
                            <i data-feather="edit" class="w-3 h-3 mr-1"></i> Edit
                        </button>
                        <button onclick="deleteMessage(${msg.id})" class="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-md flex items-center transition">
                            <i data-feather="trash-2" class="w-3 h-3 mr-1"></i>
                        </button>
                    ` : ''}
                    ${isApproved ? `
                        <button onclick="sendMessage(${msg.id})" class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md flex items-center transition">
                            <i data-feather="send" class="w-3 h-3 mr-1"></i> Send Now
                        </button>
                        <button onclick="unapproveMessage(${msg.id})" class="text-xs bg-gray-500 hover:bg-gray-600 text-white px-3 py-1.5 rounded-md transition">
                            Unapprove
                        </button>
                    ` : ''}
                ` : `
                    <span class="text-xs text-green-600 flex items-center">
                        <i data-feather="check-circle" class="w-3 h-3 mr-1"></i> Message sent
                    </span>
                `}
            </div>
        </div>
    `;
}

/**
 * Approve a message
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
        } else {
            showNotification(data.message || 'Failed to approve message', 'error');
        }
    } catch (error) {
        console.error('Error approving message:', error);
        showNotification('Error approving message', 'error');
    }
}

/**
 * Unapprove a message (set back to draft)
 */
async function unapproveMessage(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}/unapprove`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Message set back to draft', 'success');
            loadMessages(currentFilter);
        } else {
            showNotification('Failed to unapprove message', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error updating message', 'error');
    }
}

/**
 * Edit a message
 */
function editMessage(messageId) {
    const contentDiv = document.getElementById(`message-content-${messageId}`);
    if (!contentDiv) return;
    
    const currentContent = contentDiv.textContent.trim();
    
    // Create textarea for editing
    contentDiv.innerHTML = `
        <textarea id="edit-textarea-${messageId}" class="w-full p-2 border border-gray-300 rounded resize-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200" rows="4">${currentContent}</textarea>
        <div class="mt-2 flex space-x-2">
            <button onclick="saveMessage(${messageId})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm flex items-center">
                <i data-feather="save" class="w-3 h-3 mr-1"></i> Save
            </button>
            <button onclick="cancelEdit(${messageId}, \`${currentContent.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)" class="bg-gray-400 hover:bg-gray-500 text-white px-3 py-1 rounded text-sm flex items-center">
                <i data-feather="x" class="w-3 h-3 mr-1"></i> Cancel
            </button>
        </div>
    `;
    
    feather.replace();
}

/**
 * Save edited message
 */
async function saveMessage(messageId) {
    const textarea = document.getElementById(`edit-textarea-${messageId}`);
    if (!textarea) return;
    
    const newContent = textarea.value.trim();
    
    if (!newContent) {
        showNotification('Message content cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/messages/${messageId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message updated!', 'success');
            loadMessages(currentFilter);
        } else {
            showNotification(data.message || 'Failed to update message', 'error');
        }
    } catch (error) {
        console.error('Error updating message:', error);
        showNotification('Error updating message', 'error');
    }
}

/**
 * Cancel editing
 */
function cancelEdit(messageId, originalContent) {
    const contentDiv = document.getElementById(`message-content-${messageId}`);
    if (contentDiv) {
        contentDiv.innerHTML = originalContent;
    }
}

/**
 * Delete a message
 */
async function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/messages/${messageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Message deleted', 'success');
            loadMessages(currentFilter);
        } else {
            showNotification('Failed to delete message', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error deleting message', 'error');
    }
}

/**
 * Send a message (placeholder - requires LinkedIn automation)
 */
async function sendMessage(messageId) {
    showNotification('🚀 LinkedIn message sending coming soon!', 'info');
    // TODO: Implement actual LinkedIn sending
}

/**
 * Load leads for dropdown filter
 */
async function loadLeadsForFilter() {
    try {
        const response = await fetch('/api/leads?limit=200');
        const data = await response.json();
        
        if (data.success) {
            populateLeadFilter(data.leads);
        }
    } catch (error) {
        console.error('Error loading leads:', error);
    }
}

/**
 * Populate lead filter dropdown
 */
function populateLeadFilter(leads) {
    const select = document.getElementById('lead-filter');
    if (!select) return;
    
    select.innerHTML = '<option value="">All Leads</option>';
    
    // Only show leads that have messages
    const leadsWithMessages = leads.filter(lead => 
        allMessages.some(msg => msg.lead_id === lead.id)
    );
    
    leadsWithMessages.forEach(lead => {
        const option = document.createElement('option');
        option.value = lead.id;
        option.textContent = `${lead.name} (${lead.company || 'No company'})`;
        select.appendChild(option);
    });
    
    select.addEventListener('change', function() {
        const leadId = this.value;
        filterMessagesByLead(leadId);
    });
}

/**
 * Filter messages by lead
 */
function filterMessagesByLead(leadId) {
    if (!leadId) {
        groupMessagesByLead();
        displayMessages();
        return;
    }
    
    // Filter to only show selected lead
    const filteredMessages = {};
    if (currentLeadMessages[leadId]) {
        filteredMessages[leadId] = currentLeadMessages[leadId];
    }
    
    const tempLeadMessages = currentLeadMessages;
    currentLeadMessages = filteredMessages;
    displayMessages();
    
    // Restore full list after display
    setTimeout(() => {
        currentLeadMessages = tempLeadMessages;
    }, 100);
}

/**
 * Show error message
 */
function showError(message) {
    const container = document.getElementById('messages-container');
    if (container) {
        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
                <i data-feather="alert-circle" class="w-12 h-12 mx-auto text-red-500 mb-4"></i>
                <p class="text-red-600 text-lg mb-2">Error</p>
                <p class="text-red-500 text-sm">${message}</p>
                <button onclick="loadMessages('${currentFilter}')" class="mt-4 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md">
                    Try Again
                </button>
            </div>
        `;
        feather.replace();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    };
    
    notification.className = `fixed top-4 right-4 ${colors[type] || colors.info} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Bulk actions
 */
function approveAllDrafts() {
    if (!confirm('Approve all draft messages?')) return;
    
    const draftMessages = allMessages.filter(msg => msg.status === 'draft');
    
    showNotification(`Approving ${draftMessages.length} messages...`, 'info');
    
    Promise.all(draftMessages.map(msg => 
        fetch(`/api/messages/${msg.id}/approve`, { method: 'POST' })
    )).then(() => {
        showNotification('✅ All messages approved!', 'success');
        loadMessages(currentFilter);
    }).catch(error => {
        showNotification('Error approving messages', 'error');
        console.error(error);
    });
}