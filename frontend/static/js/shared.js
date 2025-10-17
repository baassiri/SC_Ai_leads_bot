/**
 * SC AI Lead Generation System - Shared JavaScript
 * Common functions used across all pages
 */

// Global state
let botStatusInterval = null;
let personasCount = 0;

/**
 * Initialize bot control buttons
 */
function initializeBotControls() {
    // Start bot button
    const startBtn = document.getElementById('start-bot-btn');
    if (startBtn) {
        startBtn.addEventListener('click', startBot);
    }
    
    // Stop bot button
    const stopBtn = document.getElementById('stop-bot-btn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopBot);
    }
}

/**
 * Initialize document upload
 */
function initializeDocumentUpload() {
    const uploadBtn = document.getElementById('upload-doc-btn');
    const fileInput = document.getElementById('file-input');
    const modal = document.getElementById('upload-modal');
    const closeModal = document.getElementById('close-upload-modal');
    
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                uploadDocument(e.target.files[0]);
            }
        });
    }
    
    if (closeModal && modal) {
        closeModal.addEventListener('click', function() {
            modal.classList.add('hidden');
            fileInput.value = ''; // Reset file input
        });
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})  // ✅ FIX: Send empty JSON object
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Bot started successfully!', 'success');
            updateBotStatus('running', 'Running');
            
            // Reload stats if on dashboard
            if (typeof loadDashboardStats === 'function') {
                setTimeout(loadDashboardStats, 2000);
            }
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
            showNotification(data.message || 'Bot stopped successfully!', 'success');
            updateBotStatus('stopped', 'Stopped');
        } else {
            showNotification(data.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showNotification('Error stopping bot', 'error');
    }
}

/**
 * Upload document
 */
async function uploadDocument(file) {
    const modal = document.getElementById('upload-modal');
    const uploadStatus = document.getElementById('upload-status');
    const uploadProgress = document.getElementById('upload-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    // Show modal
    modal.classList.remove('hidden');
    uploadProgress.classList.remove('hidden');
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        progressText.textContent = 'Uploading document...';
        progressBar.style.width = '30%';
        
        // Upload file
        const response = await fetch('/api/upload-targets', {
            method: 'POST',
            body: formData
        });
        
        progressBar.style.width = '60%';
        progressText.textContent = 'AI analyzing document...';
        
        const data = await response.json();
        
        progressBar.style.width = '100%';
        
        if (data.success) {
            progressText.textContent = `✅ Success! Extracted ${data.personas_saved} personas`;
            showNotification(data.message, 'success');
            
            // Update personas count
            loadPersonasCount();
            
            // Close modal after delay
            setTimeout(() => {
                modal.classList.add('hidden');
                uploadProgress.classList.add('hidden');
                progressBar.style.width = '0%';
            }, 2000);
        } else {
            progressText.textContent = '❌ Upload failed';
            showNotification(data.message || 'Failed to upload document', 'error');
        }
    } catch (error) {
        console.error('Error uploading document:', error);
        progressText.textContent = '❌ Upload error';
        showNotification('Error uploading document', 'error');
    }
}

/**
 * Load personas count
 */
async function loadPersonasCount() {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();
        
        if (data.success) {
            personasCount = data.total || 0;
            
            // Update sidebar count
            const countElement = document.getElementById('sidebar-personas-count');
            if (countElement) {
                countElement.textContent = personasCount;
            }
            
            // Update all other persona count elements
            document.querySelectorAll('[id*="personas-count"]').forEach(el => {
                if (el.id !== 'sidebar-personas-count') {
                    el.textContent = personasCount;
                }
            });
        }
    } catch (error) {
        console.error('Error loading personas count:', error);
    }
}

/**
 * Start polling bot status
 */
function startBotStatusPolling() {
    // Poll every 3 seconds
    botStatusInterval = setInterval(checkBotStatus, 3000);
    
    // Check immediately
    checkBotStatus();
}

/**
 * Check bot status
 */
async function checkBotStatus() {
    try {
        const response = await fetch('/api/bot/status');
        const data = await response.json();
        
        if (data.success && data.status) {
            const status = data.status.running ? 'running' : 'stopped';
            const text = data.status.current_activity || (data.status.running ? 'Running' : 'Stopped');
            
            updateBotStatus(status, text);
        }
    } catch (error) {
        // Silently fail - don't spam console
    }
}

/**
 * Update bot status indicator
 */
function updateBotStatus(status, text) {
    const indicator = document.getElementById('bot-status-indicator');
    const statusText = document.getElementById('bot-status-text');
    
    if (indicator && statusText) {
        // Remove all status classes
        indicator.classList.remove('status-running', 'status-stopped');
        
        // Add appropriate class
        if (status === 'running') {
            indicator.classList.add('status-running');
        } else {
            indicator.classList.add('status-stopped');
        }
        
        // Update text
        statusText.textContent = text;
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    
    const colors = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500',
        'warning': 'bg-yellow-500'
    };
    
    const bgColor = colors[type] || colors.info;
    
    notification.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg mb-2 transform transition-all duration-300`;
    notification.innerHTML = `
        <div class="flex items-center">
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Fade out and remove
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Format time ago
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
 * Capitalize first letter
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Get score class for styling
 */
function getScoreClass(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
}

/**
 * Get status class for styling
 */
function getStatusClass(status) {
    const classes = {
        'new': 'bg-blue-100 text-blue-800',
        'contacted': 'bg-purple-100 text-purple-800',
        'replied': 'bg-green-100 text-green-800',
        'archived': 'bg-gray-100 text-gray-800'
    };
    return classes[status] || classes.new;
}

/**
 * Generate Messages for Selected Leads
 */
async function generateMessages(leadIds = []) {
    try {
        showNotification('Generating AI messages...', 'info');
        
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_ids: leadIds })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Messages generated successfully!', 'success');
            
            // Redirect to messages page after a delay
            setTimeout(() => {
                window.location.href = '/messages';
            }, 1500);
        } else {
            showNotification(data.message || 'Failed to generate messages', 'error');
        }
    } catch (error) {
        console.error('Error generating messages:', error);
        showNotification('Error generating messages', 'error');
    }
}

/**
 * Auto-select top leads
 */
async function autoSelectTopLeads(limit = 20, minScore = 70) {
    try {
        showNotification('Selecting top leads...', 'info');
        
        const response = await fetch('/api/leads/auto-select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit, min_score: minScore })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            return data.selected_ids;
        } else {
            showNotification(data.message || 'Failed to select leads', 'error');
            return [];
        }
    } catch (error) {
        console.error('Error selecting leads:', error);
        showNotification('Error selecting leads', 'error');
        return [];
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeBotControls();
    initializeDocumentUpload();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (botStatusInterval) {
        clearInterval(botStatusInterval);
    }
});

console.log('Shared.js loaded successfully');