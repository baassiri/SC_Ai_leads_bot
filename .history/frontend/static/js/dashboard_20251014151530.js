/**
 * SC AI Lead Generation System - Dashboard JavaScript
 * Fixed version with proper lead limits and target profile support
 */

// Global state
let updateInterval = null;
let activityInterval = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Load initial data
    loadDashboardStats();
    loadActivityLogs();
    loadRecentLeads(); // Load top 5 qualified leads
    
    // Start auto-refresh intervals
    updateInterval = setInterval(function() {
        loadDashboardStats();
        loadRecentLeads();
    }, 10000); // Every 10 seconds
    
    activityInterval = setInterval(loadActivityLogs, 5000); // Every 5 seconds
    
    // Set up event listeners
    setupEventListeners();
    
    // Replace feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    console.log('Dashboard initialized successfully');
});

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Bot start button
    const startBtn = document.getElementById('start-bot');
    if (startBtn) {
        startBtn.addEventListener('click', startBot);
    }
    
    // Bot stop button
    const stopBtn = document.getElementById('stop-bot');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopBot);
    }
}

/**
 * Start the bot - FIXED TO SEND TARGET PROFILE
 */
async function startBot() {
    try {
        // Get target profile from dropdown (if exists)
        let targetProfile = '';
        const targetSelect = document.getElementById('target-profile-select');
        if (targetSelect) {
            targetProfile = targetSelect.value;
            console.log('Selected target profile:', targetProfile);
        }
        
        showNotification('Starting bot...', 'info');
        
        const response = await fetch('/api/bot/start', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({
                target_profile: targetProfile  // ✅ SEND IT!
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Bot started!', 'success');
            loadDashboardStats();
        } else {
            showNotification(data.message || 'Failed to start bot', 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Error starting bot', 'error');
    }
}

/**
 * Stop the bot
 */
async function stopBot() {
    try {
        showNotification('Stopping bot...', 'info');
        
        const response = await fetch('/api/bot/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Bot stopped!', 'success');
            loadDashboardStats();
        } else {
            showNotification(data.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Error stopping bot', 'error');
    }
}

/**
 * Load dashboard statistics
 */
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (data.success && data.stats) {
            updateStatCard('total-leads', data.stats.total_leads || 0);
            updateStatCard('qualified-leads', data.stats.qualified_leads || 0);
            updateStatCard('messages-sent', data.stats.messages_sent || 0);
            
            const replyRate = data.stats.reply_rate || 0;
            updateStatCard('response-rate', replyRate.toFixed(1) + '%');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

/**
 * Update a stat card value
 */
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Load recent high-scoring leads (LIMIT 5)
 */
async function loadRecentLeads() {
    try {
        // IMPORTANT: Only get 5 leads
        const response = await fetch('/api/leads?min_score=70&limit=5');
        const data = await response.json();
        
        if (data.success && data.leads) {
            // Double check we only show 5
            const topFive = data.leads.slice(0, 5);
            displayRecentLeads(topFive);
        } else {
            console.warn('No leads data returned');
        }
    } catch (error) {
        console.error('Error loading recent leads:', error);
    }
}

/**
 * Display recent leads in UI
 */
function displayRecentLeads(leads) {
    const container = document.querySelector('.top-leads-container');
    if (!container) {
        console.warn('Top leads container not found');
        return;
    }
    
    if (!leads || leads.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                </svg>
                <p>No qualified leads yet</p>
                <p class="text-sm mt-1">Start the bot to begin scraping!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = leads.map(lead => {
        const scoreColor = getScoreColor(lead.ai_score);
        const initials = getInitials(lead.name);
        
        return `
            <div class="flex items-center py-3 px-4 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors" onclick="window.location.href='/leads?id=${lead.id}'">
                <div class="w-10 h-10 rounded-full ${scoreColor} flex items-center justify-center text-white font-semibold mr-3 flex-shrink-0">
                    ${initials}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${lead.name}</p>
                    <p class="text-xs text-gray-500 truncate">${lead.title || 'No title'} ${lead.company ? 'at ' + lead.company : ''}</p>
                </div>
                <div class="ml-3 flex-shrink-0">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreBadgeColor(lead.ai_score)}">
                        ${Math.round(lead.ai_score)}
                    </span>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Get initials from name
 */
function getInitials(name) {
    if (!name) return '??';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

/**
 * Get score background color
 */
function getScoreColor(score) {
    if (score >= 90) return 'bg-green-600';
    if (score >= 80) return 'bg-green-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-gray-500';
}

/**
 * Get score badge color
 */
function getScoreBadgeColor(score) {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 80) return 'bg-green-50 text-green-700';
    if (score >= 70) return 'bg-blue-100 text-blue-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
}

/**
 * Load activity logs
 */
async function loadActivityLogs() {
    try {
        const response = await fetch('/api/activity-logs?limit=10');
        const data = await response.json();
        
        if (data.success && data.logs) {
            displayActivityLogs(data.logs);
        }
    } catch (error) {
        console.error('Error loading activity logs:', error);
    }
}

/**
 * Display activity logs
 */
function displayActivityLogs(logs) {
    const container = document.getElementById('activity-feed');
    if (!container) return;
    
    if (!logs || logs.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent activity</p>';
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const statusClass = getStatusClass(log.status);
        const icon = getActivityIcon(log.activity_type);
        const timeAgo = getTimeAgo(log.created_at);
        
        return `
            <div class="flex items-start space-x-3 ${statusClass}">
                <i data-feather="${icon}" class="w-4 h-4 mt-1"></i>
                <div class="flex-1">
                    <p class="text-sm">${log.description}</p>
                    <p class="text-xs text-gray-500">${timeAgo}</p>
                </div>
            </div>
        `;
    }).join('');
    
    // Refresh feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Get status CSS class
 */
function getStatusClass(status) {
    const classes = {
        'success': 'log-success',
        'error': 'log-error',
        'warning': 'log-warning',
        'info': 'log-info'
    };
    return classes[status] || 'log-info';
}

/**
 * Get activity icon
 */
function getActivityIcon(activityType) {
    const icons = {
        'bot_started': 'play',
        'bot_stopped': 'square',
        'lead_scraped': 'user-plus',
        'lead_scored': 'star',
        'message_generated': 'message-square',
        'message_sent': 'send',
        'message_approved': 'check',
        'credentials_saved': 'key',
        'file_upload': 'upload'
    };
    return icons[activityType] || 'activity';
}

/**
 * Get relative time string
 */
function getTimeAgo(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        return mins + (mins === 1 ? ' minute ago' : ' minutes ago');
    }
    if (seconds < 86400) {
        const hours = Math.floor(seconds / 3600);
        return hours + (hours === 1 ? ' hour ago' : ' hours ago');
    }
    const days = Math.floor(seconds / 86400);
    return days + (days === 1 ? ' day ago' : ' days ago');
}

/**
 * Show notification toast
 */
function showNotification(message, type) {
    const notification = document.createElement('div');
    
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const bgColor = colors[type] || colors.info;
    
    notification.className = 'fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white ' + bgColor;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
    }, 3000);
    
    setTimeout(function() {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3500);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (updateInterval) clearInterval(updateInterval);
    if (activityInterval) clearInterval(activityInterval);
});

console.log('Dashboard module loaded successfully');