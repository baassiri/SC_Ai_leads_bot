/**
 * SC AI Lead Generation System - Analytics Dashboard
 * Real-time charts and metrics with Chart.js
 */

// Chart instances
let messagesTrendChart = null;
let variantPerformanceChart = null;
let leadQualityChart = null;

/**
 * Initialize analytics dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    loadAnalytics();
    initializeCharts();
    
    // Auto-refresh every 30 seconds
    setInterval(loadAnalytics, 30000);
});

/**
 * Load analytics data from API
 */
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (data.success) {
            updateKPIs(data.stats);
            updateCharts(data.stats);
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

/**
 * Update KPI cards
 */
function updateKPIs(stats) {
    // Update KPI values
    document.getElementById('total-leads').textContent = stats.total_leads || 0;
    document.getElementById('qualified-leads').textContent = stats.qualified_leads || 0;
    document.getElementById('messages-sent').textContent = stats.messages_sent || 0;
    document.getElementById('reply-rate').textContent = (stats.reply_rate || 0).toFixed(1) + '%';
    
    // Calculate and display trends (mock for now)
    updateTrend('leads-trend', 12);
    updateTrend('qualified-trend', 8);
    updateTrend('messages-trend', 15);
    updateTrend('reply-trend', -3);
}

/**
 * Update trend indicator
 */
function updateTrend(elementId, percentChange) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const isPositive = percentChange >= 0;
    const arrow = isPositive ? '↑' : '↓';
    const colorClass = isPositive ? 'text-green-600' : 'text-red-600';
    
    element.className = `text-sm ${colorClass}`;
    element.textContent = `${arrow} ${Math.abs(percentChange)}% vs last week`;
}

/**
 * Initialize all charts
 */
function initializeCharts() {
    initMessagesOverTimeChart();
    initVariantPerformanceChart();
    initLeadQualityChart();
}

/**
 * Initialize Messages Over Time chart (Line Chart)
 */
function initMessagesOverTimeChart() {
    const ctx = document.getElementById('messages-trend-chart');
    if (!ctx) return;
    
    // Sample data (replace with real API data)
    const data = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
            {
                label: 'Messages Sent',
                data: [12, 19, 15, 25, 22, 18, 24],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Replies',
                data: [3, 5, 4, 8, 6, 4, 7],
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                tension: 0.4,
                fill: true
            }
        ]
    };
    
    messagesTrendChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Messages & Replies Over Time',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Initialize Variant Performance chart (Bar Chart)
 */
function initVariantPerformanceChart() {
    const ctx = document.getElementById('variant-performance-chart');
    if (!ctx) return;
    
    // Sample data (replace with real API data)
    const data = {
        labels: ['Variant A', 'Variant B', 'Variant C'],
        datasets: [
            {
                label: 'Sent',
                data: [45, 52, 48],
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: 'rgb(59, 130, 246)',
                borderWidth: 1
            },
            {
                label: 'Replies',
                data: [12, 18, 15],
                backgroundColor: 'rgba(34, 197, 94, 0.7)',
                borderColor: 'rgb(34, 197, 94)',
                borderWidth: 1
            },
            {
                label: 'Meetings',
                data: [3, 6, 4],
                backgroundColor: 'rgba(168, 85, 247, 0.7)',
                borderColor: 'rgb(168, 85, 247)',
                borderWidth: 1
            }
        ]
    };
    
    variantPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'A/B/C Test Performance',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Initialize Lead Quality Distribution chart (Doughnut Chart)
 */
function initLeadQualityChart() {
    const ctx = document.getElementById('lead-quality-chart');
    if (!ctx) return;
    
    // Sample data (replace with real API data)
    const data = {
        labels: ['High Quality (90-100)', 'Good (70-89)', 'Medium (50-69)', 'Low (<50)'],
        datasets: [{
            data: [15, 42, 28, 15],
            backgroundColor: [
                'rgba(34, 197, 94, 0.8)',   // Green
                'rgba(59, 130, 246, 0.8)',  // Blue
                'rgba(251, 191, 36, 0.8)',  // Yellow
                'rgba(239, 68, 68, 0.8)'    // Red
            ],
            borderColor: [
                'rgb(34, 197, 94)',
                'rgb(59, 130, 246)',
                'rgb(251, 191, 36)',
                'rgb(239, 68, 68)'
            ],
            borderWidth: 2
        }]
    };
    
    leadQualityChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Lead Quality Distribution',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

/**
 * Update charts with new data
 */
function updateCharts(stats) {
    // TODO: Update charts with real-time data
    // For now, charts use sample data
    
    // You would update like this:
    // messagesTrendChart.data.datasets[0].data = stats.messages_by_day;
    // messagesTrendChart.update();
}

/**
 * Export analytics report
 */
function exportReport() {
    window.print();
}

/**
 * Refresh analytics data
 */
function refreshAnalytics() {
    // Show loading indicator
    const btn = document.querySelector('[onclick="refreshAnalytics()"]');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-feather="loader" class="w-4 h-4 animate-spin"></i>';
        feather.replace();
    }
    
    // Reload data
    loadAnalytics().then(() => {
        // Re-enable button
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-feather="refresh-cw" class="w-4 h-4"></i>';
            feather.replace();
        }
        
        showNotification('✅ Analytics refreshed', 'success');
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        console.log(message);
    }
}