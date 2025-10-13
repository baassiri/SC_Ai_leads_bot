/**
 * Message Scheduling Interface - Simplified Version
 */

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/messages') {
        initScheduling();
        loadScheduleStats();
        setInterval(loadScheduleStats, 30000); // Refresh every 30 seconds
    }
});

/**
 * Initialize scheduling functionality
 */
function initScheduling() {
    // Add schedule button to toolbar
    addScheduleButton();
    
    // Create modal HTML
    createScheduleModal();
    
    // Initialize feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Add schedule button to toolbar
 */
function addScheduleButton() {
    const toolbar = document.querySelector('.bg-white.rounded-lg.shadow.p-4.mb-6 .flex.flex-wrap.gap-3');
    
    if (toolbar && !document.getElementById('schedule-all-btn')) {
        const scheduleBtn = document.createElement('button');
        scheduleBtn.id = 'schedule-all-btn';
        scheduleBtn.className = 'bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md text-sm flex items-center transition';
        scheduleBtn.innerHTML = '<i data-feather="calendar" class="w-4 h-4 mr-2"></i> Schedule All Approved';
        scheduleBtn.onclick = openScheduleModal;
        
        toolbar.appendChild(scheduleBtn);
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

/**
 * Create schedule modal
 */
function createScheduleModal() {
    if (document.getElementById('scheduleModal')) {
        return; // Already exists
    }
    
    const modal = document.createElement('div');
    modal.id = 'scheduleModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-50';
    modal.style.display = 'none';
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="bg-purple-500 text-white px-6 py-4 rounded-t-lg flex items-center justify-between">
                <h3 class="text-lg font-semibold flex items-center">
                    <i data-feather="calendar" class="w-5 h-5 mr-2"></i>
                    Schedule Messages
                </h3>
                <button onclick="closeScheduleModal()" class="text-white hover:text-gray-200">
                    <i data-feather="x" class="w-5 h-5"></i>
                </button>
            </div>
            
            <!-- Body -->
            <div class="p-6">
                <div class="mb-4">
                    <p class="text-gray-700 mb-4">
                        <strong id="schedule-message-count">0 messages</strong> will be scheduled
                    </p>
                    
                    <!-- Schedule Options -->
                    <div class="space-y-4">
                        <!-- Send Now -->
                        <label class="flex items-center cursor-pointer">
                            <input type="radio" name="scheduleMode" value="now" checked class="mr-3">
                            <div>
                                <div class="font-medium">Send ASAP</div>
                                <div class="text-sm text-gray-500">Respecting rate limits (15/hour, 50/day)</div>
                            </div>
                        </label>
                        
                        <!-- Schedule Later -->
                        <label class="flex items-center cursor-pointer">
                            <input type="radio" name="scheduleMode" value="later" class="mr-3">
                            <div>
                                <div class="font-medium">Schedule for Later</div>
                                <div class="text-sm text-gray-500">Pick specific time</div>
                            </div>
                        </label>
                        
                        <!-- Time Picker (Hidden by default) -->
                        <div id="timePickerSection" class="ml-8 space-y-3 hidden">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                                <input type="datetime-local" id="scheduleStartTime" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Spread Over</label>
                                <select id="scheduleSpreadHours" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                    <option value="2">2 hours</option>
                                    <option value="4">4 hours</option>
                                    <option value="8" selected>8 hours (full workday)</option>
                                    <option value="12">12 hours</option>
                                    <option value="24">24 hours</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- AI Optimization -->
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" id="scheduleAIOptimize" checked class="mr-3">
                            <div>
                                <div class="font-medium">AI Optimize Send Times</div>
                                <div class="text-sm text-gray-500">Best times: 10-11 AM, 2-3 PM</div>
                            </div>
                        </label>
                    </div>
                </div>
                
                <!-- Info Box -->
                <div class="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
                    <div class="flex items-start">
                        <i data-feather="info" class="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0"></i>
                        <div class="text-blue-800">
                            <strong>Smart Scheduling:</strong><br>
                            • Max 15 messages/hour<br>
                            • Max 50 messages/day<br>
                            • Business hours: 9 AM - 6 PM<br>
                            • Skips weekends automatically
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="bg-gray-50 px-6 py-4 rounded-b-lg flex justify-end space-x-3">
                <button onclick="closeScheduleModal()" class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100">
                    Cancel
                </button>
                <button onclick="confirmSchedule()" class="px-4 py-2 bg-purple-500 text-white rounded-md hover:bg-purple-600 flex items-center">
                    <i data-feather="check" class="w-4 h-4 mr-2"></i>
                    Schedule Messages
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    const radios = modal.querySelectorAll('input[name="scheduleMode"]');
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            const timePickerSection = document.getElementById('timePickerSection');
            if (this.value === 'later') {
                timePickerSection.classList.remove('hidden');
            } else {
                timePickerSection.classList.add('hidden');
            }
        });
    });
    
    // Set default time (1 hour from now)
    const defaultTime = new Date();
    defaultTime.setHours(defaultTime.getHours() + 1);
    document.getElementById('scheduleStartTime').value = defaultTime.toISOString().slice(0, 16);
    
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

/**
 * Open schedule modal
 */
function openScheduleModal() {
    // Get approved messages
    fetch('/api/messages?status=approved')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.messages && data.messages.length > 0) {
                const count = data.messages.length;
                document.getElementById('schedule-message-count').textContent = `${count} approved message${count !== 1 ? 's' : ''}`;
                
                const modal = document.getElementById('scheduleModal');
                modal.style.display = 'flex';
                modal.classList.remove('hidden');
                
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            } else {
                showNotification('No approved messages to schedule', 'warning');
            }
        })
        .catch(error => {
            console.error('Error loading messages:', error);
            showNotification('Error loading messages', 'danger');
        });
}

/**
 * Close schedule modal
 */
function closeScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    modal.style.display = 'none';
    modal.classList.add('hidden');
}

/**
 * Confirm and execute scheduling
 */
async function confirmSchedule() {
    const mode = document.querySelector('input[name="scheduleMode"]:checked').value;
    const aiOptimize = document.getElementById('scheduleAIOptimize').checked;
    
    let startTime = null;
    let spreadHours = 8;
    
    if (mode === 'later') {
        startTime = document.getElementById('scheduleStartTime').value;
        spreadHours = parseInt(document.getElementById('scheduleSpreadHours').value);
    }
    
    // Show loading
    const btn = document.querySelector('#scheduleModal button[onclick="confirmSchedule()"]');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="animate-spin mr-2">⏳</span> Scheduling...';
    btn.disabled = true;
    
    try {
        // Get approved messages
        const messagesResponse = await fetch('/api/messages?status=approved');
        const messagesData = await messagesResponse.json();
        
        if (!messagesData.success || !messagesData.messages || messagesData.messages.length === 0) {
            throw new Error('No approved messages found');
        }
        
        const messageIds = messagesData.messages.map(m => m.id);
        
        // Schedule batch
        const response = await fetch('/api/schedule/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_ids: messageIds,
                start_time: startTime,
                spread_hours: spreadHours,
                ai_optimize: aiOptimize
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✅ ${data.total_scheduled} messages scheduled successfully!`, 'success');
            closeScheduleModal();
            loadScheduleStats();
            
            // Refresh messages list
            if (typeof loadMessages === 'function') {
                loadMessages();
            }
        } else {
            throw new Error(data.message || 'Failed to schedule messages');
        }
    } catch (error) {
        console.error('Scheduling error:', error);
        showNotification('❌ ' + error.message, 'danger');
    } finally {
        // Restore button
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

/**
 * Load and display schedule statistics
 */
async function loadScheduleStats() {
    try {
        const response = await fetch('/api/schedule/stats');
        const data = await response.json();
        
        if (data.success) {
            updateScheduleStatsDisplay(data.stats);
        }
    } catch (error) {
        console.error('Error loading schedule stats:', error);
    }
}

/**
 * Update schedule stats display
 */
function updateScheduleStatsDisplay(stats) {
    // Remove existing widget
    const existingWidget = document.getElementById('scheduleStatsWidget');
    if (existingWidget) {
        existingWidget.remove();
    }
    
    // Create new widget
    const widget = document.createElement('div');
    widget.id = 'scheduleStatsWidget';
    widget.className = 'bg-white rounded-lg shadow p-4 mb-6';
    widget.innerHTML = `
        <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-800 flex items-center">
                <i data-feather="clock" class="w-5 h-5 mr-2 text-purple-500"></i>
                Schedule Status
            </h3>
            <button onclick="loadScheduleStats()" class="text-gray-400 hover:text-gray-600">
                <i data-feather="refresh-cw" class="w-4 h-4"></i>
            </button>
        </div>
        <div class="grid grid-cols-4 gap-4 mt-4">
            <div class="text-center">
                <div class="text-2xl font-bold text-purple-600">${stats.scheduled || 0}</div>
                <div class="text-xs text-gray-500">Scheduled</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-blue-600">${stats.next_hour || 0}</div>
                <div class="text-xs text-gray-500">Next Hour</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-green-600">${stats.today || 0}</div>
                <div class="text-xs text-gray-500">Today</div>
            </div>
            <div class="text-center">
                <div class="text-2xl font-bold text-gray-600">${stats.sent || 0}</div>
                <div class="text-xs text-gray-500">Sent</div>
            </div>
        </div>
    `;
    
    // Insert at the top of messages container
    const container = document.getElementById('messages-container');
    if (container) {
        container.parentElement.insertBefore(widget, container);
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const colors = {
        success: 'bg-green-500',
        danger: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in`;
    notification.innerHTML = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'all 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Make functions globally available
window.openScheduleModal = openScheduleModal;
window.closeScheduleModal = closeScheduleModal;
window.confirmSchedule = confirmSchedule;
window.loadScheduleStats = loadScheduleStats;