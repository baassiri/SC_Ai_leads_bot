/**
 * SC AI Lead Generation System - Messages JavaScript
 * Handles message loading, approval, editing, and sending
 */

let allMessages = [];
let currentLeadMessages = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMessages();
    loadLeads();
});

/**
 * Load all messages from API
 */
async function loadMessages(status = 'draft') {
    try {
        const response = await fetch(`/api/messages?status=${status}&limit=100`);
        const data = await response.json();
        
        if (data.success) {
            allMessages = data.messages;
            groupMessagesByLead();
            displayMessages();
        } else {
            showNotification('Failed to load messages', 'error');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        showNotification('Error loading messages', 'error');
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
                lead_name: msg.lead_name,
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
                <p class="text-gray-500 text-lg">No messages generated yet</p>
                <p class="text-gray-400 text-sm mt-2">Generate messages for your leads first</p>
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
    card.className = 'bg-white rounded-lg shadow-md p-6 mb-6';
    
    const leadName = data.lead_name || 'Unknown Lead';
    const messages = data.messages;
    
    // Group by variant
    const variants = {};
    messages.forEach(msg => {
        const variant = msg.variant || 'A';
        if (!variants[variant]) variants[variant] = [];
        variants[variant].push(msg);
    });
    
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-lg font-semibold text-gray-900">${leadName}</h3>
                <p class="text-sm text-gray-500">Lead ID: ${leadId}</p>
            </div>
            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                ${messages.length} messages
            </span>
        </div>
        
        <div class="space-y-4">
            ${Object.entries(variants).map(([variant, msgs]) => createVariantSection(variant, msgs)).join('')}
        </div>
    `;
    
    return card;
}

/**
 * Create a section for a message variant
 */
function createVariantSection(variant, messages) {
    const msg = messages[0]; // Get first message of this variant
    
    const isApproved = msg.status === 'approved';
    const isSent = msg.status === 'sent';
    
    return `
        <div class="border border-gray-200 rounded-lg p-4 ${isApproved ? 'border-green-500 bg-green-50' : ''}">
            <div class="flex justify-between items-start mb-2">
                <div class="flex items-center space-x-2">
                    <span class="font-semibold text-blue-600">Variant ${variant}</span>
                    <span class="text-xs px-2 py-1 rounded ${
                        isSent ? 'bg-green-100 text-green-800' :
                        isApproved ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-600'
                    }">
                        ${isSent ? 'Sent' : isApproved ? 'Approved' : 'Draft'}
                    </span>
                </div>
                <span class="text-xs text-gray-500">${msg.content.length} chars</span>
            </div>
            
            <div class="bg-white rounded p-3 mb-3 text-gray-700" id="message-content-${msg.id}">
                ${msg.content}
            </div>
            
            <div class="flex items-center space-x-2">
                ${!isSent ? `
                    ${!isApproved ? `
                        <button onclick="approveMessage(${msg.id})" class="text-sm bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded flex items-center">
                            <i data-feather="check" class="w-3 h-3 mr-1"></i> Approve
                        </button>
                        <button onclick="editMessage(${msg.id})" class="text-sm bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded flex items-center">
                            <i data-feather="edit" class="w-3 h-3 mr-1"></i> Edit
                        </button>
                    ` : `
                        <button onclick="sendMessage(${msg.id})" class="text-sm bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded flex items-center">
                            <i data-feather="send" class="w-3 h-3 mr-1"></i> Send Now
                        </button>
                        <button onclick="unapproveMessage(${msg.id})" class="text-sm bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded">
                            Unapprove
                        </button>
                    `}
                ` : ''}
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
            showNotification('Message approved!', 'success');
            loadMessages(); // Reload to update UI
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
        const response = await fetch(`/api/messages/${messageId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'draft' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Message set back to draft', 'success');
            loadMessages();
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
        <textarea id="edit-textarea-${messageId}" class="w-full p-2 border border-gray-300 rounded resize-none" rows="4">${currentContent}</textarea>
        <div class="mt-2 flex space-x-2">
            <button onclick="saveMessage(${messageId})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                Save
            </button>
            <button onclick="cancelEdit(${messageId}, \`${currentContent.replace(/`/g, '\\`')}\`)" class="bg-gray-400 hover:bg-gray-500 text-white px-3 py-1 rounded text-sm">
                Cancel
            </button>
        </div>
    `;
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
            loadMessages();
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
 * Send a message (placeholder - requires LinkedIn automation)
 */
async function sendMessage(messageId) {
    showNotification('LinkedIn message sending coming soon!', 'info');
    // TODO: Implement actual LinkedIn sending
}

/**
 * Load leads for dropdown
 */
async function loadLeads() {
    try {
        const response = await fetch('/api/leads');
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
    
    leads.forEach(lead => {
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
        loadMessages();
        return;
    }
    
    const container = document.getElementById('messages-container');
    if (!container) return;
    
    container.innerHTML = '<div class="text-center py-8">Loading...</div>';
    
    fetch(`/api/leads/${leadId}/messages`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                allMessages = data.messages.map(msg => ({
                    ...msg,
                    lead_name: currentLeadMessages[leadId]?.lead_name || 'Selected Lead'
                }));
                groupMessagesByLead();
                displayMessages();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error filtering messages', 'error');
        });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'error' ? 'bg-red-500 text-white' : 
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}