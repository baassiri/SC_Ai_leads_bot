/**
 * SC AI Lead Generation System - Dashboard JavaScript
 * Clean version without syntax errors
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
    
    // Start auto-refresh intervals
    updateInterval = setInterval(loadDashboardStats, 10000); // Every 10 seconds
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
 * Start the bot
 */
async function startBot() {
    try {
        showNotification('Starting bot...', 'info');
        
        const response = await fetch('/api/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
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
    if (seconds < 3600) return Math.floor(seconds / 60) + ' minutes ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    return Math.floor(seconds / 86400) + ' days ago';
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

console.log('Dashboard module loaded successfully');