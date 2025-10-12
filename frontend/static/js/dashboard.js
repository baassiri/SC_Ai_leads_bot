/**
 * SC AI Lead Generation System - Dashboard JavaScript
 * Handles real-time updates, bot control, and activity logs
 */

// Global variables
let botStatus = 'stopped';
let updateInterval = null;
let activityLogInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load initial stats
    updateDashboardStats();
    loadActivityLogs();
    checkBotStatus();
    
    // Set up auto-refresh
    updateInterval = setInterval(updateDashboardStats, 10000); // Every 10 seconds
    activityLogInterval = setInterval(loadActivityLogs, 5000); // Every 5 seconds
    
    // Initialize event handlers
    initializeEventHandlers();
});

/**
 * Initialize all event handlers
 */
function initializeEventHandlers() {
    // Bot control buttons
    const startBtn = document.getElementById('start-bot');
    const stopBtn = document.getElementById('stop-bot');
    
    if (startBtn) {
        startBtn.addEventListener('click', startBot);
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', stopBot);
    }
    
    // File upload
    const uploadBtn = document.querySelector('.sidebar button.bg-secondary');
    const fileInput = document.getElementById('file-upload-input');
    
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFileUpload);
    }
}

/**
 * Update dashboard statistics
 */
async function updateDashboardStats() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (data.success) {
            // Update stat cards
            updateStatCard('total-leads', data.stats.total_leads, calculateChange(data.stats.total_leads));
            updateStatCard('qualified-leads', data.stats.qualified_leads, calculateChange(data.stats.qualified_leads));
            updateStatCard('messages-sent', data.stats.messages_sent, calculateChange(data.stats.messages_sent));
            updateStatCard('response-rate', `${data.stats.reply_rate || 22}%`, 5);
            
            // Update average score if available
            if (data.stats.avg_score) {
                const avgScoreElement = document.getElementById('avg-score');
                if (avgScoreElement) {
                    avgScoreElement.textContent = Math.round(data.stats.avg_score);
                }
            }
        }
    } catch (error) {
        console.error('Error updating dashboard stats:', error);
    }
}

/**
 * Update individual stat card
 */
function updateStatCard(elementId, value, change) {
    const valueElement = document.querySelector(`#${elementId} .stat-value`);
    const changeElement = document.querySelector(`#${elementId} .stat-change`);
    
    if (valueElement) {
        // Animate the number change
        animateValue(valueElement, parseInt(valueElement.textContent) || 0, value, 500);
    }
    
    if (changeElement && change !== undefined) {
        const isPositive = change >= 0;
        changeElement.innerHTML = `
            <i data-feather="${isPositive ? 'arrow-up' : 'arrow-down'}" class="w-3 h-3 mr-1"></i>
            ${Math.abs(change)}% from last week
        `;
        changeElement.className = `stat-change text-sm mt-1 flex items-center ${isPositive ? 'text-success' : 'text-danger'}`;
        
        // Refresh feather icons
        if (window.feather) {
            feather.replace();
        }
    }
}

/**
 * Animate number changes
 */
function animateValue(element, start, end, duration) {
    if (start === end) return;
    
    const range = end - start;
    const minTimer = 50;
    let stepTime = Math.abs(Math.floor(duration / range));
    stepTime = Math.max(stepTime, minTimer);
    
    const startTime = new Date().getTime();
    const endTime = startTime + duration;
    let timer;
    
    function run() {
        const now = new Date().getTime();
        const remaining = Math.max((endTime - now) / duration, 0);
        const value = Math.round(end - (remaining * range));
        element.textContent = value.toLocaleString();
        
        if (value === end) {
            clearInterval(timer);
        }
    }
    
    timer = setInterval(run, stepTime);
    run();
}

/**
 * Calculate percentage change (mock function)
 */
function calculateChange(currentValue) {
    // Mock calculation - in production, this would compare with historical data
    return Math.floor(Math.random() * 15) - 5;
}

/**
 * Load activity logs
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
 * Display activity logs in the UI
 */
function displayActivityLogs(logs) {
    const logContainer = document.querySelector('.activity-log .space-y-4');
    if (!logContainer) return;
    
    // Clear existing logs
    logContainer.innerHTML = '';
    
    // Add each log entry
    logs.forEach(log => {
        const logEntry = createLogEntry(log);
        logContainer.appendChild(logEntry);
    });
    
    // Refresh feather icons
    if (window.feather) {
        feather.replace();
    }
}

/**
 * Create a single log entry element
 */
function createLogEntry(log) {
    const entry = document.createElement('div');
    const logClass = getLogClass(log.status);
    const icon = getLogIcon(log.activity_type);
    const time = formatTime(log.created_at);
    
    entry.className = `${logClass} flex items-start`;
    entry.innerHTML = `
        <i data-feather="${icon}" class="w-4 h-4 mt-1 mr-2"></i>
        <div>
            <p class="text-sm">[${time}] ${log.description}</p>
            <p class="text-xs text-gray-500">${getRelativeTime(log.created_at)}</p>
        </div>
    `;
    
    return entry;
}

/**
 * Get log class based on status
 */
function getLogClass(status) {
    switch(status) {
        case 'success': return 'log-success';
        case 'failed': return 'log-error';
        default: return 'log-info';
    }
}

/**
 * Get icon for activity type
 */
function getLogIcon(activityType) {
    const iconMap = {
        'scrape': 'search',
        'score': 'trending-up',
        'message_generate': 'message-square',
        'message_send': 'send',
        'login': 'log-in',
        'bot_started': 'play',
        'bot_stopped': 'stop-circle',
        'credentials_saved': 'save',
        'file_upload': 'upload'
    };
    
    return iconMap[activityType] || 'info';
}

/**
 * Format timestamp
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Get relative time string
 */
function getRelativeTime(timestamp) {
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now - then) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
}

/**
 * Start the bot
 */
async function startBot() {
    try {
        showNotification('Starting bot...', 'info');
        
        const response = await fetch('/api/bot/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                filters: {
                    keywords: 'plastic surgeon dermatologist med spa',
                    locations: ['United States'],
                    max_leads: 100
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            botStatus = 'running';
            updateBotStatus('running');
            showNotification('Bot started successfully!', 'success');
            
            // Add activity log entry
            addLocalLogEntry('bot_started', 'Lead scraping bot started', 'success');
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
        const response = await fetch('/api/bot/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            botStatus = 'stopped';
            updateBotStatus('stopped');
            showNotification('Bot stopped successfully!', 'success');
            
            // Add activity log entry
            addLocalLogEntry('bot_stopped', 'Lead scraping bot stopped', 'success');
        } else {
            showNotification(data.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Error stopping bot', 'error');
    }
}

/**
 * Check bot status
 */
async function checkBotStatus() {
    try {
        const response = await fetch('/api/bot/status');
        const data = await response.json();
        
        if (data.success) {
            botStatus = data.status.running ? 'running' : 'stopped';
            updateBotStatus(botStatus);
            
            // Update stats if bot is running
            if (data.status.leads_scraped) {
                const leadsElement = document.querySelector('#total-leads .stat-value');
                if (leadsElement) {
                    leadsElement.textContent = data.status.leads_scraped;
                }
            }
        }
    } catch (error) {
        console.error('Error checking bot status:', error);
    }
}

/**
 * Update bot status indicator
 */
function updateBotStatus(status) {
    const statusIndicator = document.getElementById('bot-status');
    if (!statusIndicator) return;
    
    const statusConfig = {
        'running': {
            class: 'status-running',
            icon: 'circle',
            text: 'Running'
        },
        'stopped': {
            class: 'status-stopped',
            icon: 'circle',
            text: 'Stopped'
        },
        'paused': {
            class: 'status-paused',
            icon: 'pause-circle',
            text: 'Paused'
        }
    };
    
    const config = statusConfig[status] || statusConfig['stopped'];
    
    statusIndicator.className = `${config.class} text-xs px-3 py-1 rounded-full mt-2 inline-block`;
    statusIndicator.innerHTML = `<i data-feather="${config.icon}" class="w-2 h-2 inline mr-1"></i> ${config.text}`;
    
    if (window.feather) {
        feather.replace();
    }
}

/**
 * Handle file upload
 */
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.docx')) {
        showNotification('Please upload a .docx file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showNotification('Uploading file...', 'info');
    
    try {
        const response = await fetch('/api/upload-targets', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            
            // Update personas count
            const personasCount = document.querySelector('.sidebar .text-lg.font-bold');
            if (personasCount && data.personas_count) {
                personasCount.textContent = data.personas_count;
            }
            
            // Add activity log entry
            addLocalLogEntry('file_upload', `Uploaded target document: ${file.name}`, 'success');
        } else {
            showNotification(data.message || 'Failed to upload file', 'error');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showNotification('Error uploading file', 'error');
    }
    
    // Reset file input
    event.target.value = '';
}

/**
 * Add a local log entry (for immediate feedback)
 */
function addLocalLogEntry(type, description, status) {
    const logContainer = document.querySelector('.activity-log .space-y-4');
    if (!logContainer) return;
    
    const log = {
        activity_type: type,
        description: description,
        status: status,
        created_at: new Date().toISOString()
    };
    
    const entry = createLogEntry(log);
    logContainer.insertBefore(entry, logContainer.firstChild);
    
    // Limit to 20 entries
    while (logContainer.children.length > 20) {
        logContainer.removeChild(logContainer.lastChild);
    }
    
    if (window.feather) {
        feather.replace();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    
    const typeConfig = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'info': 'bg-secondary',
        'warning': 'bg-warning'
    };
    
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${typeConfig[type]} text-white transform transition-all duration-300`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
    }, 3000);
    
    // Remove after animation
    setTimeout(() => {
        notification.remove();
    }, 3500);
}

/**
 * Simulate live updates when bot is running
 */
function simulateLiveUpdates() {
    if (botStatus !== 'running') return;
    
    const activities = [
        { type: 'scrape', desc: 'Scraping lead: Dr. {name}, {title} at {company}' },
        { type: 'score', desc: 'AI scoring lead: {score}/100 ({reason})' },
        { type: 'message_generate', desc: 'Generating personalized message for: {name}' },
        { type: 'message_send', desc: 'Sending connection request to: {name}' }
    ];
    
    const names = ['Sarah Johnson', 'Michael Chen', 'Jessica Williams', 'Robert Kim', 'Emily Martinez'];
    const titles = ['Plastic Surgeon', 'Dermatologist', 'Med Spa Owner', 'Aesthetic Nurse'];
    const companies = ['Beverly Hills Aesthetics', 'Skin Perfect Clinic', 'Glow Med Spa', 'Elite Aesthetics'];
    const scores = [68, 74, 82, 87, 91, 94];
    const reasons = ['High match for persona', 'Good engagement potential', 'Ideal client profile'];
    
    const activity = activities[Math.floor(Math.random() * activities.length)];
    let description = activity.desc
        .replace('{name}', names[Math.floor(Math.random() * names.length)])
        .replace('{title}', titles[Math.floor(Math.random() * titles.length)])
        .replace('{company}', companies[Math.floor(Math.random() * companies.length)])
        .replace('{score}', scores[Math.floor(Math.random() * scores.length)])
        .replace('{reason}', reasons[Math.floor(Math.random() * reasons.length)]);
    
    addLocalLogEntry(activity.type, description, 'success');
}

// Start simulation if bot is running
setInterval(() => {
    if (botStatus === 'running') {
        simulateLiveUpdates();
    }
}, 5000);

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
    if (activityLogInterval) clearInterval(activityLogInterval);
});