/**
 * Lead Timeline UI
 * Shows complete activity timeline for a lead
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeTimelineUI();
});

/**
 * Initialize timeline functionality
 */
function initializeTimelineUI() {
    // Create timeline modal
    createTimelineModal();
    
    // Add timeline buttons to leads
    addTimelineButtons();
}

/**
 * Create timeline modal HTML
 */
function createTimelineModal() {
    if (document.getElementById('timelineModal')) {
        return; // Already exists
    }
    
    const modal = document.createElement('div');
    modal.id = 'timelineModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-50';
    modal.style.display = 'none';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
            <!-- Header -->
            <div class="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-4 flex items-center justify-between">
                <div class="flex items-center">
                    <i data-feather="clock" class="w-6 h-6 mr-3"></i>
                    <div>
                        <h2 class="text-xl font-bold" id="timeline-lead-name">Lead Timeline</h2>
                        <p class="text-sm text-blue-100" id="timeline-lead-title"></p>
                    </div>
                </div>
                <button onclick="closeTimelineModal()" class="text-white hover:text-gray-200">
                    <i data-feather="x" class="w-6 h-6"></i>
                </button>
            </div>
            
            <!-- Summary Stats -->
            <div class="bg-gray-50 px-6 py-4 border-b">
                <div class="grid grid-cols-4 gap-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600" id="stat-total-events">0</div>
                        <div class="text-xs text-gray-600">Total Events</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-purple-600" id="stat-messages-generated">0</div>
                        <div class="text-xs text-gray-600">Messages</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-green-600" id="stat-messages-sent">0</div>
                        <div class="text-xs text-gray-600">Sent</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-orange-600" id="stat-replies">0</div>
                        <div class="text-xs text-gray-600">Replies</div>
                    </div>
                </div>
            </div>
            
            <!-- Timeline Content -->
            <div class="flex-1 overflow-y-auto p-6">
                <div id="timeline-loading" class="text-center py-12">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p class="text-gray-600">Loading timeline...</p>
                </div>
                
                <div id="timeline-error" class="hidden text-center py-12">
                    <i data-feather="alert-circle" class="w-12 h-12 text-red-500 mx-auto mb-4"></i>
                    <p class="text-red-600">Failed to load timeline</p>
                </div>
                
                <div id="timeline-content" class="hidden">
                    <!-- Timeline will be populated here -->
                </div>
            </div>
            
            <!-- Footer -->
            <div class="bg-gray-50 px-6 py-4 border-t flex justify-between">
                <button onclick="exportTimeline()" class="text-blue-600 hover:text-blue-800 flex items-center">
                    <i data-feather="download" class="w-4 h-4 mr-2"></i>
                    Export Timeline
                </button>
                <button onclick="closeTimelineModal()" class="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-md">
                    Close
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Add timeline buttons to lead cards
 */
function addTimelineButtons() {
    // This should be called after leads are loaded
    // Add click handlers to any existing timeline buttons
    document.querySelectorAll('[data-timeline-lead-id]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const leadId = parseInt(this.getAttribute('data-timeline-lead-id'));
            openTimelineModal(leadId);
        });
    });
}

/**
 * Open timeline modal for a lead
 */
async function openTimelineModal(leadId) {
    const modal = document.getElementById('timelineModal');
    modal.style.display = 'flex';
    modal.classList.remove('hidden');
    
    // Show loading
    document.getElementById('timeline-loading').style.display = 'block';
    document.getElementById('timeline-error').style.display = 'none';
    document.getElementById('timeline-content').style.display = 'none';
    
    // Store current lead ID
    window.currentTimelineLeadId = leadId;
    
    try {
        // Fetch timeline data
        const response = await fetch(`/api/leads/${leadId}/timeline`);
        const data = await response.json();
        
        if (data.success) {
            // Fetch lead details
            const leadResponse = await fetch(`/api/leads/${leadId}`);
            const leadData = await leadResponse.json();
            
            // Fetch summary
            const summaryResponse = await fetch(`/api/leads/${leadId}/timeline/summary`);
            const summaryData = await summaryResponse.json();
            
            // Update modal content
            renderTimeline(data.timeline, leadData.lead, summaryData.summary);
        } else {
            showTimelineError();
        }
    } catch (error) {
        console.error('Error loading timeline:', error);
        showTimelineError();
    }
}

/**
 * Close timeline modal
 */
function closeTimelineModal() {
    const modal = document.getElementById('timelineModal');
    modal.style.display = 'none';
    modal.classList.add('hidden');
}

/**
 * Render timeline content
 */
function renderTimeline(timeline, lead, summary) {
    // Hide loading
    document.getElementById('timeline-loading').style.display = 'none';
    document.getElementById('timeline-content').style.display = 'block';
    
    // Update header
    document.getElementById('timeline-lead-name').textContent = lead.name || 'Unknown Lead';
    document.getElementById('timeline-lead-title').textContent = `${lead.title || ''} at ${lead.company || ''}`;
    
    // Update stats
    document.getElementById('stat-total-events').textContent = summary.total_events || 0;
    document.getElementById('stat-messages-generated').textContent = summary.messages_generated || 0;
    document.getElementById('stat-messages-sent').textContent = summary.messages_sent || 0;
    document.getElementById('stat-replies').textContent = summary.replies_received || 0;
    
    // Render timeline events
    const timelineContent = document.getElementById('timeline-content');
    timelineContent.innerHTML = '';
    
    if (timeline.length === 0) {
        timelineContent.innerHTML = `
            <div class="text-center py-12">
                <i data-feather="inbox" class="w-12 h-12 text-gray-400 mx-auto mb-4"></i>
                <p class="text-gray-600">No activity yet</p>
            </div>
        `;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        return;
    }
    
    // Create timeline
    const timelineHTML = timeline.map((event, index) => {
        const isLast = index === timeline.length - 1;
        const colorClass = getColorClass(event.color);
        const iconName = event.icon || 'circle';
        
        return `
            <div class="flex ${isLast ? '' : 'mb-6'}">
                <!-- Timeline line -->
                <div class="flex flex-col items-center mr-4">
                    <div class="${colorClass} rounded-full p-2">
                        <i data-feather="${iconName}" class="w-4 h-4 text-white"></i>
                    </div>
                    ${!isLast ? '<div class="w-0.5 bg-gray-300 flex-1 my-2"></div>' : ''}
                </div>
                
                <!-- Event content -->
                <div class="flex-1 ${isLast ? '' : 'pb-4'}">
                    <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="font-semibold text-gray-800">${event.title}</h4>
                            <span class="text-xs text-gray-500">${formatTimeAgo(event.timestamp)}</span>
                        </div>
                        <p class="text-sm text-gray-600">${event.description}</p>
                        <div class="text-xs text-gray-400 mt-2">${formatDateTime(event.timestamp)}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    timelineContent.innerHTML = timelineHTML;
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Show timeline error
 */
function showTimelineError() {
    document.getElementById('timeline-loading').style.display = 'none';
    document.getElementById('timeline-error').style.display = 'block';
    document.getElementById('timeline-content').style.display = 'none';
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Export timeline
 */
async function exportTimeline() {
    const leadId = window.currentTimelineLeadId;
    
    try {
        const response = await fetch(`/api/leads/${leadId}/timeline/export`);
        const data = await response.json();
        
        if (data.success) {
            // Create download
            const blob = new Blob([JSON.stringify(data.export, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `lead-${leadId}-timeline-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            showNotification('Timeline exported successfully', 'success');
        } else {
            showNotification('Failed to export timeline', 'error');
        }
    } catch (error) {
        console.error('Error exporting timeline:', error);
        showNotification('Error exporting timeline', 'error');
    }
}

/**
 * Get color class for event type
 */
function getColorClass(color) {
    const colors = {
        'blue': 'bg-blue-500',
        'green': 'bg-green-500',
        'yellow': 'bg-yellow-500',
        'red': 'bg-red-500',
        'purple': 'bg-purple-500',
        'gray': 'bg-gray-500',
        'orange': 'bg-orange-500'
    };
    return colors[color] || 'bg-gray-500';
}

/**
 * Format time ago
 */
function formatTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        return `${mins} minute${mins === 1 ? '' : 's'} ago`;
    }
    if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        return `${hours} hour${hours === 1 ? '' : 's'} ago`;
    }
    const days = Math.floor(seconds / 86400);
    if (days < 30) {
        return `${days} day${days === 1 ? '' : 's'} ago`;
    }
    const months = Math.floor(days / 30);
    return `${months} month${months === 1 ? '' : 's'} ago`;
}

/**
 * Format date time
 */
function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Reuse existing notification system if available
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
        return;
    }
    
    // Fallback notification
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Make functions globally available
window.openTimelineModal = openTimelineModal;
window.closeTimelineModal = closeTimelineModal;
window.exportTimeline = exportTimeline;
window.addTimelineButtons = addTimelineButtons;

console.log('Lead Timeline UI loaded');