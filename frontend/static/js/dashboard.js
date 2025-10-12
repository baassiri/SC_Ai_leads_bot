/**
 * SC AI Lead Generation System - Dashboard JavaScript
 * Complete dashboard functionality with backend integration
 */

// ==========================================
// GLOBAL STATE
// ==========================================

let botStatusInterval = null;
let dashboardStatsInterval = null;
let activityLogInterval = null;

// ==========================================
// INITIALIZATION
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Dashboard initializing...');
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Load initial data
    loadDashboardStats();
    loadBotStatus();
    loadActivityLogs();
    loadRecentLeads();
    
    // Start polling for updates
    startPolling();
    
    // Attach event listeners
    attachEventListeners();
    
    console.log('✅ Dashboard initialized');
});

// ==========================================
// EVENT LISTENERS
// ==========================================

function attachEventListeners() {
    // Bot control buttons
    const startBotBtn = document.getElementById('start-bot-btn');
    const stopBotBtn = document.getElementById('stop-bot-btn');
    
    if (startBotBtn) {
        startBotBtn.addEventListener('click', startBot);
    }
    
    if (stopBotBtn) {
        stopBotBtn.addEventListener('click', stopBot);
    }
    
    // Refresh buttons
    const refreshStatsBtn = document.getElementById('refresh-stats');
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', () => {
            loadDashboardStats();
            showNotification('Stats refreshed', 'success');
        });
    }
    
    // Export button
    const exportBtn = document.getElementById('export-leads-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportLeads);
    }
}

// ==========================================
// BOT STATUS & CONTROL
// ==========================================

/**
 * Load current bot status from backend
 */
async function loadBotStatus() {
    try {
        const response = await fetch('/api/bot/status');
        const data = await response.json();
        
        if (data.success !== false) {
            updateBotStatusUI(data);
        }
    } catch (error) {
        console.error('Error loading bot status:', error);
        updateBotStatusUI({ running: false, current_activity: 'Error loading status' });
    }
}

/**
 * Update bot status UI elements
 */
function updateBotStatusUI(status) {
    // Update status indicator
    const statusIndicator = document.getElementById('bot-status-indicator');
    const statusText = document.getElementById('bot-status-text');
    const activityText = document.getElementById('bot-activity-text');
    const leadsScrapedText = document.getElementById('leads-scraped-count');
    const progressBar = document.getElementById('bot-progress-bar');
    const progressPercent = document.getElementById('bot-progress-percent');
    
    if (statusIndicator) {
        if (status.running) {
            statusIndicator.classList.remove('bg-gray-400');
            statusIndicator.classList.add('bg-green-500');
        } else {
            statusIndicator.classList.remove('bg-green-500');
            statusIndicator.classList.add('bg-gray-400');
        }
    }
    
    if (statusText) {
        statusText.textContent = status.running ? 'Running' : 'Stopped';
        statusText.className = status.running ? 'text-green-600 font-semibold' : 'text-gray-600';
    }
    
    if (activityText) {
        activityText.textContent = status.current_activity || 'Idle';
    }
    
    if (leadsScrapedText) {
        leadsScrapedText.textContent = status.leads_scraped || 0;
    }
    
    if (progressBar) {
        const progress = status.progress || 0;
        progressBar.style.width = progress + '%';
    }
    
    if (progressPercent) {
        progressPercent.textContent = (status.progress || 0) + '%';
    }
    
    // Show/hide control buttons
    const startBtn = document.getElementById('start-bot-btn');
    const stopBtn = document.getElementById('stop-bot-btn');
    
    if (startBtn && stopBtn) {
        if (status.running) {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
        } else {
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
        }
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
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Bot started successfully!', 'success');
            loadBotStatus();
        } else {
            showNotification(data.message || 'Failed to start bot', 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showNotification('Error starting bot: ' + error.message, 'error');
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
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Bot stopped successfully!', 'success');
            loadBotStatus();
        } else {
            showNotification(data.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Error stopping bot: ' + error.message, 'error');
    }
}

// ==========================================
// DASHBOARD STATISTICS
// ==========================================

/**
 * Load dashboard statistics
 */
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (data.success) {
            updateStatsCards(data.stats);
        } else {
            console.error('Failed to load dashboard stats:', data.message);
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

/**
 * Update statistics cards
 */
function updateStatsCards(stats) {
    // Total Leads
    updateStatCard('total-leads', stats.total_leads || 0, 'Total Leads');
    
    // Qualified Leads
    updateStatCard('qualified-leads', stats.qualified_leads || 0, 'Qualified Leads');
    
    // Messages Sent
    updateStatCard('messages-sent', stats.messages_sent || 0, 'Messages Sent');
    
    // Reply Rate
    const replyRate = stats.reply_rate || 0;
    updateStatCard('reply-rate', replyRate.toFixed(1) + '%', 'Reply Rate');
    
    // Average Score
    const avgScore = stats.avg_score || 0;
    updateStatCard('avg-score', avgScore.toFixed(1), 'Avg. Lead Score');
    
    // Conversion Rate
    const conversionRate = stats.total_leads > 0 
        ? ((stats.qualified_leads / stats.total_leads) * 100).toFixed(1)
        : 0;
    updateStatCard('conversion-rate', conversionRate + '%', 'Conversion Rate');
    
    // Update trend indicators
    updateTrendIndicators(stats);
}

/**
 * Update a single stat card
 */
function updateStatCard(elementId, value, label) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
    
    // Also update the label if it exists
    const labelElement = document.getElementById(elementId + '-label');
    if (labelElement) {
        labelElement.textContent = label;
    }
}

/**
 * Update trend indicators (up/down arrows)
 */
function updateTrendIndicators(stats) {
    // This would compare with previous period
    // For now, we'll show positive trends for qualified leads
    
    const trends = {
        'total-leads-trend': stats.total_leads > 0 ? 'up' : 'neutral',
        'qualified-leads-trend': stats.qualified_leads > 0 ? 'up' : 'neutral',
        'messages-sent-trend': stats.messages_sent > 0 ? 'up' : 'neutral',
        'reply-rate-trend': stats.reply_rate > 15 ? 'up' : 'down'
    };
    
    Object.keys(trends).forEach(trendId => {
        const element = document.getElementById(trendId);
        if (element) {
            const direction = trends[trendId];
            
            if (direction === 'up') {
                element.innerHTML = '<i data-feather="trending-up" class="w-4 h-4 text-green-500"></i>';
            } else if (direction === 'down') {
                element.innerHTML = '<i data-feather="trending-down" class="w-4 h-4 text-red-500"></i>';
            } else {
                element.innerHTML = '<i data-feather="minus" class="w-4 h-4 text-gray-400"></i>';
            }
            
            // Re-render feather icons
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }
    });
}

// ==========================================
// ACTIVITY LOGS
// ==========================================

/**
 * Load recent activity logs
 */
async function loadActivityLogs() {
    try {
        const response = await fetch('/api/activity-logs?limit=10');
        const data = await response.json();
        
        if (data.success) {
            displayActivityLogs(data.logs);
        }
    } catch (error) {
        console.error('Error loading activity logs:', error);
    }
}

/**
 * Display activity logs in the feed
 */
function displayActivityLogs(logs) {
    const container = document.getElementById('activity-feed');
    
    if (!container) return;
    
    if (!logs || logs.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i data-feather="inbox" class="w-8 h-8 mx-auto mb-2"></i>
                <p>No recent activity</p>
            </div>
        `;
        if (typeof feather !== 'undefined') feather.replace();
        return;
    }
    
    container.innerHTML = logs.map(log => {
        const timeAgo = getTimeAgo(log.created_at);
        const statusColor = getStatusColor(log.status);
        const activityIcon = getActivityIcon(log.activity_type);
        
        return `
            <div class="flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg transition">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 rounded-full ${statusColor} flex items-center justify-center">
                        <i data-feather="${activityIcon}" class="w-4 h-4 text-white"></i>
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900">${log.description}</p>
                    ${log.error_message ? `<p class="text-xs text-red-600 mt-1">${log.error_message}</p>` : ''}
                    <p class="text-xs text-gray-500 mt-1">${timeAgo}</p>
                </div>
            </div>
        `;
    }).join('');
    
    // Re-render feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Get status color class
 */
function getStatusColor(status) {
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    };
    return colors[status] || 'bg-gray-500';
}

/**
 * Get activity icon name
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
        'document_uploaded': 'upload',
        'personas_extracted': 'users'
    };
    return icons[activityType] || 'activity';
}

/**
 * Convert timestamp to relative time
 */
function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return time.toLocaleDateString();
}

// ==========================================
// RECENT LEADS
// ==========================================

/**
 * Load recent high-scoring leads
 */
async function loadRecentLeads() {
    try {
        const response = await fetch('/api/leads?min_score=70&limit=5&sort=created_at');
        const data = await response.json();
        
        if (data.success) {
            displayRecentLeads(data.leads);
        }
    } catch (error) {
        console.error('Error loading recent leads:', error);
    }
}

/**
 * Display recent leads
 */
function displayRecentLeads(leads) {
    const container = document.getElementById('recent-leads');
    
    if (!container) return;
    
    if (!leads || leads.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i data-feather="user-x" class="w-12 h-12 mx-auto mb-2"></i>
                <p>No leads yet. Start the bot to begin scraping!</p>
            </div>
        `;
        if (typeof feather !== 'undefined') feather.replace();
        return;
    }
    
    container.innerHTML = leads.map(lead => {
        const scoreClass = getScoreClass(lead.ai_score);
        const scoreColor = getScoreColor(lead.ai_score);
        
        return `
            <div class="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition"
                 onclick="viewLeadDetail(${lead.id})">
                <div class="flex items-center space-x-3 flex-1 min-w-0">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(lead.name)}&background=random" 
                         alt="${lead.name}" 
                         class="w-10 h-10 rounded-full">
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 truncate">${lead.name}</p>
                        <p class="text-xs text-gray-500 truncate">${lead.title || 'No title'} at ${lead.company || 'Unknown'}</p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full ${scoreColor}">
                        ${lead.ai_score || 0}
                    </span>
                    <i data-feather="chevron-right" class="w-4 h-4 text-gray-400"></i>
                </div>
            </div>
        `;
    }).join('');
    
    // Re-render feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Get score class for styling
 */
function getScoreClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
}

/**
 * Get score color classes
 */
function getScoreColor(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-blue-100 text-blue-800';
    if (score >= 40) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
}

/**
 * View lead detail (redirect to leads page)
 */
function viewLeadDetail(leadId) {
    window.location.href = `/leads?id=${leadId}`;
}

// ==========================================
// EXPORT FUNCTIONALITY
// ==========================================

/**
 * Export leads to CSV
 */
async function exportLeads() {
    try {
        showNotification('Preparing export...', 'info');
        
        const response = await fetch('/api/leads/export');
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `leads_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('Leads exported successfully!', 'success');
    } catch (error) {
        console.error('Error exporting leads:', error);
        showNotification('Error exporting leads: ' + error.message, 'error');
    }
}

// ==========================================
// POLLING & AUTO-REFRESH
// ==========================================

/**
 * Start polling for updates
 */
function startPolling() {
    // Bot status - every 3 seconds
    botStatusInterval = setInterval(loadBotStatus, 3000);
    
    // Dashboard stats - every 30 seconds
    dashboardStatsInterval = setInterval(loadDashboardStats, 30000);
    
    // Activity logs - every 10 seconds
    activityLogInterval = setInterval(loadActivityLogs, 10000);
}

/**
 * Stop polling (cleanup)
 */
function stopPolling() {
    if (botStatusInterval) clearInterval(botStatusInterval);
    if (dashboardStatsInterval) clearInterval(dashboardStatsInterval);
    if (activityLogInterval) clearInterval(activityLogInterval);
}

// Cleanup on page unload
window.addEventListener('beforeunload', stopPolling);

// ==========================================
// NOTIFICATION SYSTEM
// ==========================================

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 ${getNotificationColor(type)}`;
    
    const icon = getNotificationIcon(type);
    
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i data-feather="${icon}" class="w-5 h-5"></i>
            <span class="font-medium">${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Render feather icon
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateY(-100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

/**
 * Get notification color classes
 */
function getNotificationColor(type) {
    const colors = {
        'success': 'bg-green-500 text-white',
        'error': 'bg-red-500 text-white',
        'warning': 'bg-yellow-500 text-white',
        'info': 'bg-blue-500 text-white'
    };
    return colors[type] || colors.info;
}

/**
 * Get notification icon
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'x-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    };
    return icons[type] || icons.info;
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==========================================
// EXPORT FOR OTHER MODULES
// ==========================================

// Make functions available globally if needed
window.dashboardFunctions = {
    startBot,
    stopBot,
    loadBotStatus,
    loadDashboardStats,
    loadActivityLogs,
    loadRecentLeads,
    exportLeads,
    showNotification
};

console.log('📊 Dashboard module loaded');