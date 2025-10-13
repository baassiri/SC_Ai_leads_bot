/**
 * Sales Navigator Integration
 */

// Load Sales Nav status on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSalesNavStatus();
});

/**
 * Load Sales Navigator configuration
 */
async function loadSalesNavStatus() {
    try {
        const response = await fetch('/api/sales-nav/config');
        const data = await response.json();
        
        if (data.success && data.config) {
            updateSalesNavUI(data.config);
        }
    } catch (error) {
        console.error('Error loading Sales Nav config:', error);
    }
}

/**
 * Update UI based on Sales Nav status
 */
function updateSalesNavUI(config) {
    const isEnabled = config.enabled;
    
    // Show/hide Sales Nav features
    document.querySelectorAll('.sales-nav-only').forEach(el => {
        el.style.display = isEnabled ? 'block' : 'none';
    });
    
    // Update status badge
    const badge = document.getElementById('sales-nav-badge');
    if (badge) {
        if (isEnabled) {
            badge.innerHTML = '🚀 Sales Nav Active';
            badge.className = 'badge bg-success';
        } else {
            badge.innerHTML = '💼 Standard LinkedIn';
            badge.className = 'badge bg-secondary';
        }
    }
    
    // Update InMail credits display
    if (isEnabled) {
        loadInMailCredits();
    }
}

/**
 * Load InMail credits
 */
async function loadInMailCredits() {
    try {
        const response = await fetch('/api/sales-nav/inmail/credits');
        const data = await response.json();
        
        if (data.success) {
            const creditsEl = document.getElementById('inmail-credits');
            if (creditsEl) {
                creditsEl.textContent = `${data.credits.remaining}/${data.credits.total}`;
            }
        }
    } catch (error) {
        console.error('Error loading InMail credits:', error);
    }
}

/**
 * Toggle Sales Navigator
 */
async function toggleSalesNav(enabled) {
    try {
        const response = await fetch('/api/sales-nav/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled: enabled,
                plan_type: 'advanced'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(
                enabled ? '✅ Sales Navigator enabled!' : '⚠️ Sales Navigator disabled',
                enabled ? 'success' : 'warning'
            );
            
            // Reload to apply changes
            setTimeout(() => location.reload(), 1000);
        }
    } catch (error) {
        showNotification('❌ Error updating Sales Navigator', 'danger');
    }
}

// Make functions globally available
window.toggleSalesNav = toggleSalesNav;
window.loadSalesNavStatus = loadSalesNavStatus;