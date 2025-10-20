/**
 * Lead Timeline UI Component
 * Displays a visual timeline of all interactions with a lead
 */

let currentLeadId = null;
let currentLeadName = '';

/**
 * Open the timeline modal for a specific lead
 */
async function openTimeline(leadId, leadName) {
    currentLeadId = leadId;
    currentLeadName = leadName;
    
    const modal = document.getElementById('timelineModal');
    const body = document.getElementById('timelineBody');
    
    // Show modal
    modal.classList.add('active');
    
    // Show loading state
    body.innerHTML = '<div class="loading">Loading timeline...</div>';
    
    try {
        const response = await fetch(`/api/leads/${leadId}/timeline`);
        const data = await response.json();
        
        if (data.success) {
            renderTimeline(data.lead, data.timeline);
        } else {
            body.innerHTML = `<div class="error">Failed to load timeline: ${data.message}</div>`;
        }
    } catch (error) {
        console.error('Error loading timeline:', error);
        body.innerHTML = '<div class="error">Error loading timeline. Please try again.</div>';
    }
}

/**
 * Close the timeline modal
 */
function closeTimeline() {
    const modal = document.getElementById('timelineModal');
    modal.classList.remove('active');
    currentLeadId = null;
    currentLeadName = '';
}

/**
 * Render the timeline view
 */
function renderTimeline(lead, events) {
    const body = document.getElementById('timelineBody');
    
    const html = `
        <div class="timeline-lead-info">
            <div class="lead-header">
                <div class="lead-avatar">${getInitials(lead.name)}</div>
                <div class="lead-details">
                    <h3>${lead.name}</h3>
                    <p>${lead.title || 'No title'} at ${lead.company || 'Unknown company'}</p>
                    <div class="lead-meta">
                        <span class="score-badge ${getScoreClass(lead.score)}">${lead.score} Score</span>
                        <span class="status-badge status-${lead.status}">${formatStatus(lead.status)}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timeline-events">
            <h3>Activity Timeline</h3>
            ${events.length > 0 ? renderEvents(events) : '<p class="no-events">No activity recorded yet.</p>'}
        </div>
    `;
    
    body.innerHTML = html;
}

/**
 * Render timeline events
 */
function renderEvents(events) {
    return `
        <div class="timeline">
            ${events.map((event, index) => `
                <div class="timeline-item ${event.type}">
                    <div class="timeline-marker">
                        <span class="timeline-icon">${event.icon}</span>
                    </div>
                    <div class="timeline-content">
                        <div class="timeline-time">${formatTimestamp(event.timestamp)}</div>
                        <div class="timeline-description">${event.description}</div>
                        ${event.status ? `<div class="timeline-status">${event.status}</div>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

/**
 * Get initials from name
 */
function getInitials(name) {
    return name
        .split(' ')
        .map(word => word[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        // Today - show time
        return 'Today at ' + date.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
    } else if (diffDays === 1) {
        return 'Yesterday at ' + date.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true 
        });
    } else if (diffDays < 7) {
        return diffDays + ' days ago';
    } else {
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
        });
    }
}

/**
 * Get score class for styling
 */
function getScoreClass(score) {
    if (score >= 70) return 'score-high';
    if (score >= 40) return 'score-medium';
    return 'score-low';
}

/**
 * Format status for display
 */
function formatStatus(status) {
    return status.replace('_', ' ').toUpperCase();
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('timelineModal');
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeTimeline();
        }
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeTimeline();
        }
    });
});

// Add CSS styles dynamically
const timelineStyles = `
    .timeline-lead-info {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .lead-header {
        display: flex;
        gap: 15px;
        align-items: start;
    }

    .lead-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
    }

    .lead-details h3 {
        margin: 0 0 5px 0;
        color: #333;
    }

    .lead-details p {
        margin: 0 0 10px 0;
        color: #666;
    }

    .lead-meta {
        display: flex;
        gap: 10px;
    }

    .timeline-events h3 {
        margin: 0 0 20px 0;
        color: #333;
    }

    .timeline {
        position: relative;
        padding-left: 40px;
    }

    .timeline::before {
        content: '';
        position: absolute;
        left: 15px;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #e0e0e0;
    }

    .timeline-item {
        position: relative;
        padding-bottom: 30px;
    }

    .timeline-marker {
        position: absolute;
        left: -40px;
        top: 0;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: white;
        border: 2px solid #667eea;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .timeline-icon {
        font-size: 16px;
    }

    .timeline-content {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }

    .timeline-time {
        font-size: 12px;
        color: #999;
        margin-bottom: 5px;
    }

    .timeline-description {
        color: #333;
        line-height: 1.5;
    }

    .timeline-status {
        margin-top: 8px;
        font-size: 12px;
        color: #666;
        font-style: italic;
    }

    .timeline-item.message_sent .timeline-marker {
        border-color: #28a745;
    }

    .timeline-item.response_received .timeline-marker {
        border-color: #17a2b8;
    }

    .timeline-item.status_change .timeline-marker {
        border-color: #ffc107;
    }

    .timeline-item.campaign_assigned .timeline-marker {
        border-color: #6f42c1;
    }

    .no-events {
        text-align: center;
        color: #999;
        padding: 40px;
    }

    .error {
        text-align: center;
        color: #dc3545;
        padding: 40px;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = timelineStyles;
document.head.appendChild(styleSheet);