let updateInterval = null;
let activityInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    loadDashboardStats();
    loadActivityLogs();
    loadRecentLeads();
    loadDetectedPersonas();
    
    updateInterval = setInterval(function() {
        loadDashboardStats();
        loadRecentLeads();
    }, 10000);
    
    activityInterval = setInterval(loadActivityLogs, 5000);
    
    setupEventListeners();
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    console.log('Dashboard initialized successfully');
});

function setupEventListeners() {
    const startBtn = document.getElementById('start-bot');
    if (startBtn) {
        startBtn.addEventListener('click', startBot);
    }
    
    const stopBtn = document.getElementById('stop-bot');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopBot);
    }
}

async function startBot() {
    try {
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
                target_profile: targetProfile
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

function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

async function loadRecentLeads() {
    try {
        const response = await fetch('/api/leads?min_score=70&limit=5');
        const data = await response.json();
        
        if (data.success && data.leads) {
            const topFive = data.leads.slice(0, 5);
            displayRecentLeads(topFive);
        } else {
            console.warn('No leads data returned');
        }
    } catch (error) {
        console.error('Error loading recent leads:', error);
    }
}

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

function getInitials(name) {
    if (!name) return '??';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
}

function getScoreColor(score) {
    if (score >= 90) return 'bg-green-600';
    if (score >= 80) return 'bg-green-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-gray-500';
}

function getScoreBadgeColor(score) {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 80) return 'bg-green-50 text-green-700';
    if (score >= 70) return 'bg-blue-100 text-blue-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
}

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
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

function getStatusClass(status) {
    const classes = {
        'success': 'log-success',
        'error': 'log-error',
        'warning': 'log-warning',
        'info': 'log-info'
    };
    return classes[status] || 'log-info';
}

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

async function loadDetectedPersonas() {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();
        
        const container = document.getElementById('personas-container');
        const loading = document.getElementById('personas-loading');
        const empty = document.getElementById('personas-empty');
        
        if (loading) loading.style.display = 'none';
        
        if (!data.success || !data.personas || data.personas.length === 0) {
            if (empty) empty.classList.remove('hidden');
            return;
        }
        
        if (empty) empty.classList.add('hidden');
        
        const personasHTML = data.personas.map(persona => `
            <div class="bg-white rounded-lg border-2 border-purple-200 p-5 hover:shadow-lg transition-shadow">
                <div class="flex items-start justify-between mb-3">
                    <div>
                        <h4 class="text-lg font-bold text-gray-800 mb-1">${escapeHtml(persona.name)}</h4>
                        <p class="text-sm text-gray-600">${escapeHtml(persona.description || 'No description')}</p>
                    </div>
                    <span class="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full">
                        ID: ${persona.id}
                    </span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div class="bg-blue-50 rounded-md p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <i data-feather="briefcase" class="w-4 h-4 text-blue-600"></i>
                            <span class="text-sm font-semibold text-gray-700">Target Job Titles</span>
                        </div>
                        <div class="text-xs text-gray-600 space-y-1">
                            ${formatList(persona.job_titles, 5)}
                        </div>
                    </div>
                    
                    <div class="bg-green-50 rounded-md p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <i data-feather="user-check" class="w-4 h-4 text-green-600"></i>
                            <span class="text-sm font-semibold text-gray-700">Decision Makers</span>
                        </div>
                        <div class="text-xs text-gray-600 space-y-1">
                            ${formatList(persona.decision_maker_roles, 5)}
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 rounded-md p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <i data-feather="building" class="w-4 h-4 text-yellow-600"></i>
                            <span class="text-sm font-semibold text-gray-700">Company Types</span>
                        </div>
                        <div class="text-xs text-gray-600 space-y-1">
                            ${formatList(persona.company_types, 5)}
                        </div>
                    </div>
                    
                    <div class="bg-purple-50 rounded-md p-3">
                        <div class="flex items-center gap-2 mb-2">
                            <i data-feather="search" class="w-4 h-4 text-purple-600"></i>
                            <span class="text-sm font-semibold text-gray-700">LinkedIn Search Keywords</span>
                        </div>
                        <div class="text-xs text-gray-600 space-y-1">
                            ${formatList(persona.linkedin_keywords, 5)}
                        </div>
                    </div>
                </div>
                
                ${persona.smart_search_query ? `
                <div class="mt-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-md p-3 border border-indigo-200">
                    <div class="flex items-center gap-2 mb-2">
                        <i data-feather="zap" class="w-4 h-4 text-indigo-600"></i>
                        <span class="text-sm font-semibold text-gray-700">AI-Optimized Search Query</span>
                    </div>
                    <p class="text-sm text-gray-700 font-mono bg-white rounded px-3 py-2 border border-indigo-100">
                        ${escapeHtml(persona.smart_search_query)}
                    </p>
                </div>
                ` : ''}
                
                <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
                    <div class="flex items-center gap-4">
                        ${persona.seniority_level ? `
                        <span class="flex items-center gap-1">
                            <i data-feather="award" class="w-3 h-3"></i>
                            ${escapeHtml(persona.seniority_level)}
                        </span>
                        ` : ''}
                        ${persona.industry_focus ? `
                        <span class="flex items-center gap-1">
                            <i data-feather="trending-up" class="w-3 h-3"></i>
                            ${escapeHtml(persona.industry_focus)}
                        </span>
                        ` : ''}
                    </div>
                    ${persona.document_source ? `
                    <span class="flex items-center gap-1 text-purple-600">
                        <i data-feather="file" class="w-3 h-3"></i>
                        ${escapeHtml(persona.document_source)}
                    </span>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        const tempDiv = document.createElement('div');
        tempDiv.className = 'space-y-4';
        tempDiv.innerHTML = personasHTML;
        
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
        container.appendChild(tempDiv);
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        console.log(`✅ Loaded ${data.personas.length} personas`);
        
    } catch (error) {
        console.error('Error loading personas:', error);
        const empty = document.getElementById('personas-empty');
        if (empty) {
            empty.classList.remove('hidden');
            empty.innerHTML = `
                <div class="text-center py-8">
                    <i data-feather="alert-circle" class="w-16 h-16 mx-auto text-red-400 mb-3"></i>
                    <h4 class="text-lg font-semibold text-gray-700 mb-2">Error Loading Personas</h4>
                    <p class="text-gray-500">${error.message}</p>
                </div>
            `;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }
    }
}

function formatList(text, maxItems = 5) {
    if (!text) return '<span class="text-gray-400 italic">Not specified</span>';
    
    const items = text.split('\n').filter(item => item.trim());
    const displayItems = items.slice(0, maxItems);
    const remaining = items.length - maxItems;
    
    let html = displayItems.map(item => 
        `<div class="flex items-start gap-1">
            <span class="text-gray-400">•</span>
            <span>${escapeHtml(item.trim())}</span>
        </div>`
    ).join('');
    
    if (remaining > 0) {
        html += `<div class="text-gray-400 italic text-xs mt-1">+ ${remaining} more...</div>`;
    }
    
    return html;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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

window.addEventListener('beforeunload', function() {
    if (updateInterval) clearInterval(updateInterval);
    if (activityInterval) clearInterval(activityInterval);
});

console.log('Dashboard module loaded successfully');