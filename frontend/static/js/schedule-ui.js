// Scheduling UI - Add to messages.js

// Schedule Modal HTML (add to messages.html)
const scheduleModalHTML = `
<div id="scheduleModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="p-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold">Schedule Messages</h2>
                <button onclick="closeScheduleModal()" class="text-gray-400 hover:text-gray-600">
                    <i data-feather="x" class="w-6 h-6"></i>
                </button>
            </div>
            
            <!-- Selected Messages Count -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p class="text-sm text-blue-800">
                    <i data-feather="info" class="w-4 h-4 inline mr-1"></i>
                    <span id="selectedCount">0</span> messages selected
                </p>
            </div>
            
            <!-- Schedule Type -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Schedule Type</label>
                <div class="grid grid-cols-2 gap-4">
                    <button onclick="setScheduleType('now')" class="schedule-type-btn active border-2 border-blue-500 bg-blue-50 rounded-lg p-4 text-left">
                        <i data-feather="zap" class="w-5 h-5 text-blue-500 mb-2"></i>
                        <h3 class="font-semibold">Send Now</h3>
                        <p class="text-sm text-gray-600">Start sending immediately</p>
                    </button>
                    <button onclick="setScheduleType('later')" class="schedule-type-btn border-2 border-gray-200 rounded-lg p-4 text-left hover:border-blue-300">
                        <i data-feather="clock" class="w-5 h-5 text-gray-500 mb-2"></i>
                        <h3 class="font-semibold">Schedule Later</h3>
                        <p class="text-sm text-gray-600">Pick specific time</p>
                    </button>
                </div>
            </div>
            
            <!-- Time Settings (shown only for 'later') -->
            <div id="timeSettings" class="hidden mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                <input type="datetime-local" id="startTime" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:border-blue-500 focus:outline-none">
            </div>
            
            <!-- Distribution -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Distribution
                    <span class="text-gray-500 text-xs ml-1">(Spread over time)</span>
                </label>
                <select id="spreadHours" class="w-full border border-gray-300 rounded-md px-3 py-2 focus:border-blue-500 focus:outline-none">
                    <option value="1">1 hour - Fast burst</option>
                    <option value="2">2 hours - Quick campaign</option>
                    <option value="4" selected>4 hours - Balanced</option>
                    <option value="8">8 hours - Full business day</option>
                    <option value="24">24 hours - Spread across day</option>
                </select>
            </div>
            
            <!-- AI Optimization -->
            <div class="mb-6">
                <label class="flex items-center">
                    <input type="checkbox" id="aiOptimize" checked class="rounded border-gray-300 text-blue-500 focus:ring-blue-500">
                    <span class="ml-2 text-sm text-gray-700">
                        Use AI to optimize send times
                        <span class="text-gray-500">(Recommended)</span>
                    </span>
                </label>
            </div>
            
            <!-- Business Hours Notice -->
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <p class="text-sm text-yellow-800">
                    <i data-feather="alert-circle" class="w-4 h-4 inline mr-1"></i>
                    Messages will only send during business hours (9 AM - 6 PM, Mon-Fri)
                </p>
            </div>
            
            <!-- Rate Limiting Info -->
            <div class="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 class="font-semibold text-sm mb-2">Rate Limits</h3>
                <ul class="text-sm text-gray-600 space-y-1">
                    <li>• Max 15 messages per hour</li>
                    <li>• Max 50 messages per day</li>
                    <li>• Min 3 minutes between messages</li>
                </ul>
            </div>
            
            <!-- Actions -->
            <div class="flex space-x-3">
                <button onclick="closeScheduleModal()" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-md">
                    Cancel
                </button>
                <button onclick="scheduleMessages()" class="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center justify-center">
                    <i data-feather="calendar" class="w-4 h-4 mr-2"></i>
                    Schedule <span id="scheduleCount" class="ml-1"></span> Messages
                </button>
            </div>
        </div>
    </div>
</div>
`;

// Add modal to page
function initScheduleModal() {
    if (!document.getElementById('scheduleModal')) {
        document.body.insertAdjacentHTML('beforeend', scheduleModalHTML);
        feather.replace();
    }
}

// Open modal
function openScheduleModal(selectedMessages) {
    initScheduleModal();
    
    const modal = document.getElementById('scheduleModal');
    const count = selectedMessages.length;
    
    document.getElementById('selectedCount').textContent = count;
    document.getElementById('scheduleCount').textContent = count;
    
    // Set default start time (now + 5 minutes)
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5);
    document.getElementById('startTime').value = now.toISOString().slice(0, 16);
    
    modal.classList.remove('hidden');
    
    // Store selected messages
    window.selectedMessagesToSchedule = selectedMessages;
}

// Close modal
function closeScheduleModal() {
    document.getElementById('scheduleModal').classList.add('hidden');
}

// Set schedule type
function setScheduleType(type) {
    const buttons = document.querySelectorAll('.schedule-type-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active', 'border-blue-500', 'bg-blue-50');
        btn.classList.add('border-gray-200');
    });
    
    event.target.closest('.schedule-type-btn').classList.add('active', 'border-blue-500', 'bg-blue-50');
    event.target.closest('.schedule-type-btn').classList.remove('border-gray-200');
    
    // Show/hide time settings
    const timeSettings = document.getElementById('timeSettings');
    if (type === 'later') {
        timeSettings.classList.remove('hidden');
    } else {
        timeSettings.classList.add('hidden');
    }
}

// Schedule messages
async function scheduleMessages() {
    const messages = window.selectedMessagesToSchedule || [];
    
    if (messages.length === 0) {
        alert('No messages selected');
        return;
    }
    
    const scheduleType = document.querySelector('.schedule-type-btn.active')
        .onclick.toString().includes('now') ? 'now' : 'later';
    
    const spreadHours = parseInt(document.getElementById('spreadHours').value);
    const aiOptimize = document.getElementById('aiOptimize').checked;
    
    let startTime = null;
    if (scheduleType === 'later') {
        startTime = document.getElementById('startTime').value;
        if (!startTime) {
            alert('Please select a start time');
            return;
        }
    }
    
    // Show loading
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i data-feather="loader" class="w-4 h-4 animate-spin"></i> Scheduling...';
    btn.disabled = true;
    
    try {
        const messageIds = messages.map(m => m.id);
        
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
            alert(`✅ Scheduled ${data.total_scheduled} messages!`);
            closeScheduleModal();
            
            // Reload messages
            if (typeof loadMessages === 'function') {
                loadMessages();
            }
        } else {
            alert('Error: ' + data.message);
        }
        
    } catch (error) {
        console.error('Schedule error:', error);
        alert('Failed to schedule messages');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        feather.replace();
    }
}

// Add schedule button to messages page
function addScheduleButton() {
    const toolbar = document.querySelector('.toolbar'); // Adjust selector as needed
    if (toolbar && !document.getElementById('scheduleBtn')) {
        const scheduleBtn = document.createElement('button');
        scheduleBtn.id = 'scheduleBtn';
        scheduleBtn.className = 'bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center';
        scheduleBtn.innerHTML = '<i data-feather="calendar" class="w-4 h-4 mr-2"></i> Schedule Selected';
        scheduleBtn.onclick = function() {
            const selected = getSelectedMessages(); // You need to implement this
            if (selected.length === 0) {
                alert('Please select messages to schedule');
                return;
            }
            openScheduleModal(selected);
        };
        toolbar.appendChild(scheduleBtn);
        feather.replace();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('messages')) {
        addScheduleButton();
    }
});