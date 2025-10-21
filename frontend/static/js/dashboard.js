let updateInterval = null;
let activityInterval = null;
let currentEditingPersona = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    loadDashboardStats();
    loadActivityLogs();
    loadRecentLeads();
    loadDetectedPersonas();
    checkBotStatus();  // ✅ ADDED: Check LinkedIn login status on load
    
    updateInterval = setInterval(function() {
        loadDashboardStats();
        loadRecentLeads();
        checkBotStatus();  // ✅ ADDED: Check status every 10 seconds
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
/**
 * Check bot status including LinkedIn connection
 */
async function checkBotStatus() {
    try {
        const response = await fetch('/api/bot/status');
        const data = await response.json();
        
        if (data.success) {
            // Update LinkedIn status in UI
            if (typeof updateLinkedInStatus === 'function') {
                updateLinkedInStatus(data.linkedin_logged_in);
            }
            
            // Update bot status if needed
            if (data.status && data.status.running) {
                // Bot is running
                const startBtn = document.getElementById('start-bot');
                const stopBtn = document.getElementById('stop-bot');
                if (startBtn) startBtn.disabled = true;
                if (stopBtn) stopBtn.disabled = false;
            } else {
                // Bot is stopped
                const startBtn = document.getElementById('start-bot');
                const stopBtn = document.getElementById('stop-bot');
                if (startBtn) startBtn.disabled = false;
                if (stopBtn) stopBtn.disabled = true;
            }
        }
    } catch (error) {
        console.error('Error checking bot status:', error);
    }
}
/**
 * Update LinkedIn connection status in UI
 */
function updateLinkedInStatus(isLoggedIn) {
    const btn = document.getElementById('linkedin-login-btn');
    if (!btn) return;
    
    if (isLoggedIn) {
        // Show as logged in
        btn.innerHTML = '<svg class="h-4 w-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Logged In';
        btn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        btn.classList.add('bg-green-600');
        btn.disabled = false;
    } else {
        // Show as not logged in
        btn.innerHTML = '<i data-feather="linkedin" class="h-4 w-4 mr-2"></i> Login to LinkedIn';
        btn.classList.remove('bg-green-600');
        btn.classList.add('bg-blue-600', 'hover:bg-blue-700');
        btn.disabled = false;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
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

// ============================================================================
// ENHANCED PERSONA CARDS - Add to dashboard.js
// Replace the loadDetectedPersonas() function with this enhanced version
// ============================================================================

async function loadDetectedPersonas() {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();

        const container = document.getElementById('personas-container');
        const loading = document.getElementById('personas-loading');
        const empty = document.getElementById('personas-empty');
        const list = document.getElementById('personas-list');

        // Hide loading
        loading.classList.add('hidden');

        if (!data.success || !data.personas || data.personas.length === 0) {
            empty.classList.remove('hidden');
            list.classList.add('hidden');
            return;
        }

        // Show personas list
        empty.classList.add('hidden');
        list.classList.remove('hidden');

        // Generate enhanced persona cards HTML
        const personasHTML = data.personas.map(persona => `
            <div class="persona-card bg-white rounded-lg border-2 border-gray-200 overflow-hidden hover:border-purple-400 transition-all">
                <!-- Header -->
                <div class="bg-gradient-to-r from-purple-500 to-pink-500 p-4">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <h4 class="text-xl font-bold text-white mb-1">${escapeHtml(persona.name)}</h4>
                            <p class="text-sm text-purple-100">${escapeHtml(persona.description || 'No description')}</p>
                        </div>
                        <span class="bg-white bg-opacity-20 text-white text-xs px-2 py-1 rounded-full">
                            ID: ${persona.id}
                        </span>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="flex gap-2 mt-3">
                        <button onclick="viewPersonaDetails(${persona.id})" 
                                class="flex-1 px-3 py-2 bg-white text-purple-600 text-sm font-semibold rounded-md hover:bg-purple-50 transition-colors flex items-center justify-center gap-1">
                            <i data-feather="eye" class="w-4 h-4"></i>
                            View
                        </button>
                        <button onclick="openEditModal(${persona.id})" 
                                class="flex-1 px-3 py-2 bg-purple-600 text-white text-sm font-semibold rounded-md hover:bg-purple-700 transition-colors flex items-center justify-center gap-1">
                            <i data-feather="edit-2" class="w-4 h-4"></i>
                            Edit
                        </button>
                        <button onclick="deletePersona(${persona.id}, '${escapeHtml(persona.name).replace(/'/g, "\\'")}

')" 
                                class="px-3 py-2 bg-red-500 text-white text-sm font-semibold rounded-md hover:bg-red-600 transition-colors flex items-center justify-center">
                            <i data-feather="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Body -->
                <div class="p-4 space-y-3">
                    <!-- Demographics Section -->
                    ${(persona.age_range || persona.gender_distribution) ? `
                    <div class="bg-blue-50 rounded-lg p-3">
                        <h5 class="text-xs font-bold text-blue-800 mb-2 flex items-center gap-1">
                            <i data-feather="user" class="w-3 h-3"></i>
                            DEMOGRAPHICS
                        </h5>
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            ${persona.age_range ? `
                                <div>
                                    <span class="text-gray-600">Age:</span>
                                    <span class="font-semibold text-gray-800">${escapeHtml(persona.age_range)}</span>
                                </div>
                            ` : ''}
                            ${persona.gender_distribution ? `
                                <div>
                                    <span class="text-gray-600">Gender:</span>
                                    <span class="font-semibold text-gray-800">${escapeHtml(persona.gender_distribution)}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Job Titles -->
                    ${persona.job_titles ? `
                    <div>
                        <h5 class="text-xs font-bold text-gray-600 mb-1 flex items-center gap-1">
                            <i data-feather="briefcase" class="w-3 h-3"></i>
                            JOB TITLES
                        </h5>
                        <div class="text-sm text-gray-700 space-y-1">
                            ${formatList(persona.job_titles, 3)}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- Company Info -->
                    <div class="grid grid-cols-2 gap-2">
                        ${persona.company_size ? `
                        <div class="bg-gray-50 rounded p-2">
                            <div class="text-xs text-gray-500 mb-1">Company Size</div>
                            <div class="text-sm font-semibold text-gray-800">${escapeHtml(persona.company_size)}</div>
                        </div>
                        ` : ''}
                        ${persona.seniority_level ? `
                        <div class="bg-gray-50 rounded p-2">
                            <div class="text-xs text-gray-500 mb-1">Seniority</div>
                            <div class="text-sm font-semibold text-gray-800">${escapeHtml(persona.seniority_level)}</div>
                        </div>
                        ` : ''}
                    </div>
                    
                    <!-- Industry -->
                    ${persona.industry_focus ? `
                    <div class="bg-green-50 rounded-lg p-2">
                        <div class="text-xs text-green-700 font-semibold mb-1">🎯 Industry Focus</div>
                        <div class="text-sm text-gray-700">${escapeHtml(persona.industry_focus)}</div>
                    </div>
                    ` : ''}
                    
                    <!-- Pain Points & Goals -->
                    ${(persona.pain_points || persona.goals) ? `
                    <div class="bg-yellow-50 rounded-lg p-3">
                        <h5 class="text-xs font-bold text-yellow-800 mb-2 flex items-center gap-1">
                            <i data-feather="target" class="w-3 h-3"></i>
                            AI SCORING
                        </h5>
                        ${persona.pain_points ? `
                            <div class="mb-2">
                                <div class="text-xs text-gray-600 font-semibold">Pain Points:</div>
                                <div class="text-xs text-gray-700">${escapeHtml(persona.pain_points).substring(0, 80)}${persona.pain_points.length > 80 ? '...' : ''}</div>
                            </div>
                        ` : ''}
                        ${persona.goals ? `
                            <div>
                                <div class="text-xs text-gray-600 font-semibold">Goals:</div>
                                <div class="text-xs text-gray-700">${escapeHtml(persona.goals).substring(0, 80)}${persona.goals.length > 80 ? '...' : ''}</div>
                            </div>
                        ` : ''}
                    </div>
                    ` : ''}
                    
                    <!-- Location -->
                    ${persona.location_data ? `
                    <div class="bg-indigo-50 rounded-lg p-2">
                        <div class="text-xs text-indigo-700 font-semibold mb-1 flex items-center gap-1">
                            <i data-feather="map-pin" class="w-3 h-3"></i>
                            Location Targeting
                        </div>
                        <div class="text-xs text-gray-700">
                            ${getLocationSummary(persona.location_data)}
                        </div>
                    </div>
                    ` : ''}
                    
                    <!-- LinkedIn Search Query -->
                    ${persona.smart_search_query ? `
                    <div class="bg-gray-100 rounded-lg p-3">
                        <h5 class="text-xs font-bold text-gray-700 mb-1 flex items-center gap-1">
                            <i data-feather="search" class="w-3 h-3"></i>
                            LINKEDIN SEARCH
                        </h5>
                        <div class="text-xs text-gray-600 font-mono bg-white rounded p-2 break-all">
                            ${escapeHtml(persona.smart_search_query)}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `).join('');

        list.innerHTML = personasHTML;

        // Replace feather icons
        setTimeout(() => {
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }, 100);

        console.log(`✅ Loaded ${data.personas.length} personas`);
    } catch (error) {
        console.error('Error loading personas:', error);
        const empty = document.getElementById('personas-empty');
        if (empty) {
            empty.innerHTML = `
                <div class="text-center py-8">
                    <i data-feather="alert-circle" class="w-16 h-16 mx-auto text-red-400 mb-3"></i>
                    <h4 class="text-lg font-semibold text-gray-700 mb-2">Error Loading Personas</h4>
                    <p class="text-gray-500 mb-4">Please refresh the page to try again</p>
                </div>
            `;
            empty.classList.remove('hidden');
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }
    }
}

// Helper function to parse and display location data
function getLocationSummary(locationData) {
    try {
        const loc = typeof locationData === 'string' ? JSON.parse(locationData) : locationData;
        
        if (loc.worldwide) {
            return '🌍 Worldwide';
        }
        
        const parts = [];
        if (loc.cities && loc.cities.length > 0) {
            parts.push(`Cities: ${loc.cities.slice(0, 2).join(', ')}${loc.cities.length > 2 ? '...' : ''}`);
        }
        if (loc.countries && loc.countries.length > 0) {
            parts.push(`Countries: ${loc.countries.slice(0, 2).join(', ')}${loc.countries.length > 2 ? '...' : ''}`);
        }
        if (loc.regions && loc.regions.length > 0) {
            parts.push(`Regions: ${loc.regions.join(', ')}`);
        }
        
        return parts.length > 0 ? parts.join(' • ') : 'Not specified';
    } catch (e) {
        return 'Not specified';
    }
}

// DELETE PERSONA FUNCTION
async function deletePersona(personaId, personaName) {
    if (!confirm(`Are you sure you want to delete "${personaName}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        showNotification('Deleting persona...', 'info');
        
        const response = await fetch(`/api/personas/${personaId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Persona deleted successfully!', 'success');
            loadDetectedPersonas(); // Reload the list
        } else {
            showNotification('❌ ' + (data.message || 'Failed to delete persona'), 'error');
        }
    } catch (error) {
        console.error('Error deleting persona:', error);
        showNotification('❌ Error deleting persona', 'error');
    }
}

// VIEW PERSONA DETAILS MODAL (placeholder - we'll build this in Step 2)
async function openEditModal(personaId) {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();
        
        if (data.success && data.personas) {
            const persona = data.personas.find(p => p.id === personaId);
            
            if (persona) {
                currentEditingPersona = persona;
                
                document.getElementById('edit-persona-id').value = persona.id;
                document.getElementById('edit-name').value = persona.name || '';
                document.getElementById('edit-description').value = persona.description || '';
                document.getElementById('edit-job-titles').value = persona.job_titles || '';
                document.getElementById('edit-decision-makers').value = persona.decision_maker_roles || '';
                document.getElementById('edit-company-types').value = persona.company_types || '';
                document.getElementById('edit-linkedin-keywords').value = persona.linkedin_keywords || '';
                document.getElementById('edit-search-query').value = persona.smart_search_query || '';
                document.getElementById('edit-seniority').value = persona.seniority_level || '';
                document.getElementById('edit-industry').value = persona.industry_focus || '';
                
                document.getElementById('edit-persona-modal').classList.remove('hidden');
                
                setTimeout(() => {
                    if (typeof feather !== 'undefined') {
                        feather.replace();
                    }
                }, 100);
            }
        }
    } catch (error) {
        console.error('Error opening edit modal:', error);
        showNotification('Error loading persona details', 'error');
    }
}

function closeEditModal() {
    document.getElementById('edit-persona-modal').classList.add('hidden');
    currentEditingPersona = null;
}

async function savePersona() {
    try {
        const personaId = document.getElementById('edit-persona-id').value;
        
        const updates = {
            name: document.getElementById('edit-name').value.trim(),
            description: document.getElementById('edit-description').value.trim(),
            job_titles: document.getElementById('edit-job-titles').value.trim(),
            decision_maker_roles: document.getElementById('edit-decision-makers').value.trim(),
            company_types: document.getElementById('edit-company-types').value.trim(),
            linkedin_keywords: document.getElementById('edit-linkedin-keywords').value.trim(),
            smart_search_query: document.getElementById('edit-search-query').value.trim(),
            seniority_level: document.getElementById('edit-seniority').value.trim(),
            industry_focus: document.getElementById('edit-industry').value.trim()
        };
        
        showNotification('Saving changes...', 'info');
        
        const response = await fetch(`/api/personas/${personaId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Persona updated successfully!', 'success');
            closeEditModal();
            loadDetectedPersonas();
        } else {
            showNotification('❌ ' + (data.message || 'Failed to update persona'), 'error');
        }
    } catch (error) {
        console.error('Error saving persona:', error);
        showNotification('❌ Error saving changes', 'error');
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
// ============================================================================
// PERSONA DETAILS MODAL - JavaScript Functions
// Add these functions to dashboard.js
// ============================================================================

let currentViewingPersona = null;

/**
 * View full persona details in modal
 */
async function viewPersonaDetails(personaId) {
    try {
        // Fetch persona data
        const response = await fetch('/api/personas');
        const data = await response.json();
        
        if (data.success && data.personas) {
            const persona = data.personas.find(p => p.id === personaId);
            
            if (persona) {
                currentViewingPersona = persona;
                populatePersonaDetailsModal(persona);
                
                // Fetch stats for this persona
                loadPersonaStats(personaId);
                
                // Show modal
                document.getElementById('persona-details-modal').classList.remove('hidden');
                
                // Replace feather icons
                setTimeout(() => {
                    if (typeof feather !== 'undefined') {
                        feather.replace();
                    }
                }, 100);
            }
        }
    } catch (error) {
        console.error('Error viewing persona details:', error);
        showNotification('Error loading persona details', 'error');
    }
}

/**
 * Populate modal with persona data
 */
function populatePersonaDetailsModal(persona) {
    // Header
    document.getElementById('detail-persona-name').textContent = persona.name || 'Unnamed Persona';
    document.getElementById('detail-persona-description').textContent = persona.description || 'No description';
    
    // Demographics
    document.getElementById('detail-age-range').textContent = persona.age_range || 'Not specified';
    document.getElementById('detail-gender').textContent = persona.gender_distribution || 'Not specified';
    
    // Job & Company
    if (persona.job_titles) {
        const titles = persona.job_titles.split('\n').filter(t => t.trim());
        document.getElementById('detail-job-titles').innerHTML = titles.map(t => 
            `<div class="flex items-start gap-1">
                <span class="text-gray-400">•</span>
                <span>${escapeHtml(t.trim())}</span>
            </div>`
        ).join('');
    } else {
        document.getElementById('detail-job-titles').innerHTML = '<span class="text-gray-400 italic">Not specified</span>';
    }
    
    document.getElementById('detail-seniority').textContent = persona.seniority_level || 'Not specified';
    document.getElementById('detail-company-size').textContent = persona.company_size || 'Not specified';
    
    if (persona.company_types) {
        const types = persona.company_types.split('\n').filter(t => t.trim());
        document.getElementById('detail-company-types').innerHTML = types.map(t => 
            `<div class="flex items-start gap-1">
                <span class="text-gray-400">•</span>
                <span>${escapeHtml(t.trim())}</span>
            </div>`
        ).join('');
    } else {
        document.getElementById('detail-company-types').innerHTML = '<span class="text-gray-400 italic">Not specified</span>';
    }
    
    document.getElementById('detail-industry').textContent = persona.industry_focus || 'Not specified';
    
    // Location
    const locationContent = getLocationDetails(persona.location_data);
    document.getElementById('detail-location-content').innerHTML = locationContent;
    
    // AI Scoring
    document.getElementById('detail-pain-points').textContent = persona.pain_points || 'Not specified';
    document.getElementById('detail-goals').textContent = persona.goals || 'Not specified';
    document.getElementById('detail-keywords').textContent = persona.linkedin_keywords || 'Not specified';
    document.getElementById('detail-decision-makers').textContent = persona.decision_maker_roles || 'Not specified';
    
    // LinkedIn Search Query
    document.getElementById('detail-search-query').textContent = persona.smart_search_query || 'Not generated';
    
    // Metadata
    document.getElementById('detail-persona-id').textContent = persona.id;
    document.getElementById('detail-created-at').textContent = formatDate(persona.created_at);
    document.getElementById('detail-updated-at').textContent = formatDate(persona.updated_at);
}

/**
 * Get detailed location information
 */
function getLocationDetails(locationData) {
    try {
        const loc = typeof locationData === 'string' ? JSON.parse(locationData) : locationData;
        
        if (loc.worldwide) {
            return '<div class="flex items-center gap-2"><span class="text-2xl">🌍</span><span class="font-semibold">Worldwide</span></div>';
        }
        
        let html = '';
        
        if (loc.regions && loc.regions.length > 0) {
            html += '<div class="mb-2"><div class="text-xs text-gray-600 font-semibold mb-1">Regions:</div>';
            html += loc.regions.map(r => `<span class="inline-block bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs mr-1 mb-1">${escapeHtml(r)}</span>`).join('');
            html += '</div>';
        }
        
        if (loc.countries && loc.countries.length > 0) {
            html += '<div class="mb-2"><div class="text-xs text-gray-600 font-semibold mb-1">Countries:</div>';
            html += loc.countries.map(c => `<span class="inline-block bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs mr-1 mb-1">${escapeHtml(c)}</span>`).join('');
            html += '</div>';
        }
        
        if (loc.cities && loc.cities.length > 0) {
            html += '<div><div class="text-xs text-gray-600 font-semibold mb-1">Cities:</div>';
            html += loc.cities.map(c => `<span class="inline-block bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs mr-1 mb-1">${escapeHtml(c)}</span>`).join('');
            html += '</div>';
        }
        
        return html || '<span class="text-gray-400 italic">Not specified</span>';
    } catch (e) {
        return '<span class="text-gray-400 italic">Not specified</span>';
    }
}

/**
 * Load stats for persona (leads, messages, etc.)
 */
async function loadPersonaStats(personaId) {
    try {
        // For now, show 0 - you'll implement the actual API endpoint later
        // This is a placeholder that you can enhance when you build the leads system
        document.getElementById('detail-leads-count').textContent = '0';
        document.getElementById('detail-qualified-count').textContent = '0';
        document.getElementById('detail-messages-count').textContent = '0';
        document.getElementById('detail-replied-count').textContent = '0';
        
        // TODO: Implement actual stats API
        // const response = await fetch(`/api/personas/${personaId}/stats`);
        // const data = await response.json();
        // if (data.success) {
        //     document.getElementById('detail-leads-count').textContent = data.stats.total_leads;
        //     document.getElementById('detail-qualified-count').textContent = data.stats.qualified_leads;
        //     document.getElementById('detail-messages-count').textContent = data.stats.messages_sent;
        //     document.getElementById('detail-replied-count').textContent = data.stats.replies;
        // }
    } catch (error) {
        console.error('Error loading persona stats:', error);
    }
}

/**
 * Close persona details modal
 */
function closePersonaDetailsModal() {
    document.getElementById('persona-details-modal').classList.add('hidden');
    currentViewingPersona = null;
}

/**
 * Copy LinkedIn search query to clipboard
 */
function copySearchQuery() {
    const query = document.getElementById('detail-search-query').textContent;
    
    if (query && query !== 'Not generated') {
        navigator.clipboard.writeText(query).then(() => {
            showNotification('✅ Search query copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Error copying to clipboard:', err);
            showNotification('❌ Failed to copy to clipboard', 'error');
        });
    } else {
        showNotification('No search query to copy', 'warning');
    }
}

/**
 * Edit persona from details modal
 */
function editFromDetails() {
    if (currentViewingPersona) {
        closePersonaDetailsModal();
        setTimeout(() => {
            openEditModal(currentViewingPersona.id);
        }, 300);
    }
}

/**
 * Delete persona from details modal
 */
function deleteFromDetails() {
    if (currentViewingPersona) {
        closePersonaDetailsModal();
        setTimeout(() => {
            deletePersona(currentViewingPersona.id, currentViewingPersona.name);
        }, 300);
    }
}

/**
 * Start lead scraping with this persona
 */
function startScrapingWithPersona() {
    if (currentViewingPersona) {
        showNotification('Lead scraping feature coming soon! 🚀', 'info');
        // TODO: Implement lead scraping
        // This will be implemented when you build the LinkedIn scraper integration
    }
}

/**
 * Format date helper
 */
function formatDate(dateString) {
    if (!dateString) return 'Not available';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return 'Invalid date';
    }
}
/**
 * LinkedIn Login Function - FIXED (No Auto-Reload)
 */
async function loginToLinkedIn() {
    console.log('🔐 LinkedIn login initiated...');
    
    const btn = document.getElementById('linkedin-login-btn');
    if (!btn) {
        console.error('LinkedIn login button not found');
        return;
    }
    
    const originalHTML = btn.innerHTML;
    
    // Show loading state
    btn.innerHTML = '<svg class="animate-spin h-4 w-4 mr-2 inline" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Connecting...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/linkedin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        console.log('LinkedIn login response:', data);
        
        if (data.success) {
            // SUCCESS!
            console.log('✅ LinkedIn login successful!');
            
            // Update button to success state
            btn.innerHTML = '<svg class="h-4 w-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Logged In';
            btn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            btn.classList.add('bg-green-600');
            
            // Show success notification
            if (typeof showNotification === 'function') {
                if (data.manual_login) {
                    showNotification('🌐 LinkedIn login page opened! Please complete login in the Chrome window.', 'info');
                } else {
                    showNotification('✅ ' + (data.message || 'LinkedIn login successful!'), 'success');
                }
            }
            
            // ✅ DON'T RELOAD - Just update the status
            // Instead of: setTimeout(() => location.reload(), 3000);
            // We'll let the status polling update the UI naturally
            
        } else {
            // FAILURE
            console.error('❌ LinkedIn login failed:', data.message);
            
            if (typeof showNotification === 'function') {
                showNotification('❌ ' + (data.message || 'Login failed'), 'error');
            }
            
            // Restore button
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }
        
    } catch (error) {
        console.error('❌ LinkedIn login error:', error);
        
        if (typeof showNotification === 'function') {
            showNotification('❌ Error connecting to LinkedIn: ' + error.message, 'error');
        }
        
        // Restore button
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

// Make it globally available
window.loginToLinkedIn = loginToLinkedIn;

console.log('✅ Improved loginToLinkedIn function loaded (no auto-reload)');