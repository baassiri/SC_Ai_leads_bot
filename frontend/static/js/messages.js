/**
 * SC AI Lead Generation System - Enhanced Messages JavaScript
 * Improved UI with custom modals and professional notifications
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
                        <button onclick="confirmDelete(${msg.id})" class="text-xs bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-md flex items-center transition">
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
 * Custom Confirmation Modal
 */
function showConfirmDialog(title, message, onConfirm, confirmText = 'Confirm', cancelText = 'Cancel') {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    overlay.id = 'confirm-modal';
    
    // Create modal
    overlay.innerHTML = `
        <div class="bg-white rounded-lg shadow-2xl max-w-md w-full transform transition-all">
            <div class="p-6">
                <div class="flex items-start space-x-4">
                    <div class="flex-shrink-0">
                        <div class="w-12 h-12 rounded-full bg-yellow-100 flex items-center justify-center">
                            <i data-feather="alert-triangle" class="w-6 h-6 text-yellow-600"></i>
                        </div>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900 mb-2">${title}</h3>
                        <p class="text-gray-600 text-sm">${message}</p>
                    </div>
                </div>
            </div>
            <div class="bg-gray-50 px-6 py-4 flex justify-end space-x-3 rounded-b-lg">
                <button id="modal-cancel" class="px-4 py-2 bg-white border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition">
                    ${cancelText}
                </button>
                <button id="modal-confirm" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition flex items-center">
                    <i data-feather="check" class="w-4 h-4 mr-2"></i>
                    ${confirmText}
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    feather.replace();
    
    // Event listeners
    document.getElementById('modal-cancel').onclick = () => overlay.remove();
    document.getElementById('modal-confirm').onclick = () => {
        onConfirm();
        overlay.remove();
    };
    
    // Click outside to close
    overlay.onclick = (e) => {
        if (e.target === overlay) overlay.remove();
    };
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
            showNotification('Message approved successfully!', 'success');
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
            showNotification('Message updated successfully!', 'success');
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
 * Confirm delete with custom modal
 */
function confirmDelete(messageId) {
    showConfirmDialog(
        'Delete Message',
        'Are you sure you want to delete this message? This action cannot be undone.',
        () => deleteMessage(messageId),
        'Delete',
        'Cancel'
    );
}

/**
 * Delete a message
 */
async function deleteMessage(messageId) {
    try {
        const response = await fetch(`/api/messages/${messageId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Message deleted successfully', 'success');
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
    // Confirm before sending
    if (!confirm('This will open LinkedIn and send this message. Continue?')) {
        return;
    }
    
    try {
        showNotification('Opening LinkedIn...', 'info');
        
        const response = await fetch(`/api/messages/${messageId}/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Message sent successfully!', 'success');
            loadMessages(currentFilter);
        } else {
            showNotification(`❌ ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('Error sending message', 'error');
    }
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
 * Professional Notification Toast
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const colors = {
        success: { bg: 'bg-green-50', border: 'border-green-500', text: 'text-green-800', icon: 'check-circle' },
        error: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-800', icon: 'x-circle' },
        info: { bg: 'bg-blue-50', border: 'border-blue-500', text: 'text-blue-800', icon: 'info' },
        warning: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-800', icon: 'alert-triangle' }
    };
    
    const style = colors[type] || colors.info;
    
    notification.className = `fixed top-4 right-4 ${style.bg} ${style.text} border-l-4 ${style.border} px-6 py-4 rounded-lg shadow-xl z-50 animate-slide-in flex items-center space-x-3 max-w-md`;
    notification.innerHTML = `
        <i data-feather="${style.icon}" class="w-5 h-5 flex-shrink-0"></i>
        <span class="font-medium">${message}</span>
        <button onclick="this.parentElement.remove()" class="ml-auto text-gray-400 hover:text-gray-600 transition">
            <i data-feather="x" class="w-4 h-4"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    feather.replace();
    
    setTimeout(() => {
        notification.style.transition = 'all 0.3s ease-out';
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

/**
 * Bulk actions - Approve all drafts
 */
function approveAllDrafts() {
    const draftMessages = allMessages.filter(msg => msg.status === 'draft');
    
    if (draftMessages.length === 0) {
        showNotification('No draft messages to approve', 'info');
        return;
    }
    
    showConfirmDialog(
        'Approve All Drafts',
        `Are you sure you want to approve all ${draftMessages.length} draft messages?`,
        () => {
            showNotification(`Approving ${draftMessages.length} messages...`, 'info');
            
            Promise.all(draftMessages.map(msg => 
                fetch(`/api/messages/${msg.id}/approve`, { method: 'POST' })
            )).then(() => {
                showNotification('All messages approved successfully!', 'success');
                loadMessages(currentFilter);
            }).catch(error => {
                showNotification('Error approving messages', 'error');
                console.error(error);
            });
        },
        'Approve All',
        'Cancel'
    );
}