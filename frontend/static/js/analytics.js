// Analytics Dashboard - Real Data
document.addEventListener('DOMContentLoaded', function() {
    loadAnalytics();
});

let charts = {};

async function loadAnalytics() {
    try {
        // Fetch all analytics data
        const [stats, leads, messages, schedule] = await Promise.all([
            fetch('/api/analytics/dashboard').then(r => r.json()),
            fetch('/api/leads').then(r => r.json()),
            fetch('/api/messages').then(r => r.json()),
            fetch('/api/schedule/stats').then(r => r.json())
        ]);
        
        updateKPIs(stats.stats, schedule.stats);
        renderLeadsOverTime(leads.leads);
        renderLeadsByPersona(leads.leads);
        renderLeadStatus(leads.leads);
        renderMessagePerformance(messages.messages);
        renderScheduleTimeline(schedule.stats);
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        showError('Failed to load analytics data');
    }
}

function updateKPIs(stats, scheduleStats) {
    // Update KPI cards
    const totalLeads = stats.total_leads || 0;
    const qualifiedLeads = stats.qualified_leads || 0;
    const avgScore = stats.avg_score || 0;
    const messagesSent = stats.messages_sent || 0;
    
    // Calculate rates
    const qualificationRate = totalLeads > 0 ? ((qualifiedLeads / totalLeads) * 100).toFixed(1) : 0;
    const scheduledMessages = scheduleStats.scheduled || 0;
    const sentToday = scheduleStats.sent_today || 0;
    
    document.getElementById('totalLeads').textContent = totalLeads;
    document.getElementById('qualifiedLeads').textContent = qualifiedLeads;
    document.getElementById('qualificationRate').textContent = qualificationRate + '%';
    document.getElementById('avgScore').textContent = avgScore.toFixed(1);
    document.getElementById('messagesSent').textContent = messagesSent;
    document.getElementById('scheduledMessages').textContent = scheduledMessages;
    document.getElementById('sentToday').textContent = sentToday;
}

function renderLeadsOverTime(leads) {
    // Group leads by date
    const dates = {};
    const today = new Date();
    
    // Initialize last 7 days
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const key = date.toISOString().split('T')[0];
        dates[key] = { total: 0, qualified: 0 };
    }
    
    // Count leads by date
    leads.forEach(lead => {
        const date = lead.created_at ? lead.created_at.split('T')[0] : null;
        if (date && dates[date]) {
            dates[date].total++;
            if (lead.ai_score >= 70) {
                dates[date].qualified++;
            }
        }
    });
    
    const labels = Object.keys(dates).map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    const totalData = Object.values(dates).map(d => d.total);
    const qualifiedData = Object.values(dates).map(d => d.qualified);
    
    const ctx = document.getElementById('leadsOverTimeChart');
    if (charts.leadsOverTime) charts.leadsOverTime.destroy();
    
    charts.leadsOverTime = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Total Leads',
                    data: totalData,
                    borderColor: '#3498DB',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Qualified (Score ≥70)',
                    data: qualifiedData,
                    borderColor: '#27AE60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderLeadsByPersona(leads) {
    // Count leads by persona
    const personaCounts = {};
    
    leads.forEach(lead => {
        const persona = lead.persona_name || 'Unknown';
        personaCounts[persona] = (personaCounts[persona] || 0) + 1;
    });
    
    const labels = Object.keys(personaCounts);
    const data = Object.values(personaCounts);
    
    const colors = [
        'rgba(52, 152, 219, 0.7)',
        'rgba(155, 89, 182, 0.7)',
        'rgba(26, 188, 156, 0.7)',
        'rgba(241, 196, 15, 0.7)',
        'rgba(231, 76, 60, 0.7)',
        'rgba(149, 165, 166, 0.7)'
    ];
    
    const ctx = document.getElementById('leadsByPersonaChart');
    if (charts.leadsByPersona) charts.leadsByPersona.destroy();
    
    charts.leadsByPersona = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Leads by Persona',
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderColor: colors.slice(0, labels.length).map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderLeadStatus(leads) {
    // Count by status
    const statusCounts = {
        'new': 0,
        'contacted': 0,
        'replied': 0,
        'archived': 0
    };
    
    leads.forEach(lead => {
        const status = lead.status || 'new';
        if (statusCounts.hasOwnProperty(status)) {
            statusCounts[status]++;
        } else {
            statusCounts['new']++;
        }
    });
    
    const ctx = document.getElementById('leadStatusChart');
    if (charts.leadStatus) charts.leadStatus.destroy();
    
    charts.leadStatus = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['New', 'Contacted', 'Replied', 'Archived'],
            datasets: [{
                data: [
                    statusCounts.new,
                    statusCounts.contacted,
                    statusCounts.replied,
                    statusCounts.archived
                ],
                backgroundColor: [
                    'rgba(52, 152, 219, 0.7)',
                    'rgba(155, 89, 182, 0.7)',
                    'rgba(26, 188, 156, 0.7)',
                    'rgba(149, 165, 166, 0.7)'
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(155, 89, 182, 1)',
                    'rgba(26, 188, 156, 1)',
                    'rgba(149, 165, 166, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

function renderMessagePerformance(messages) {
    // Count by variant
    const variantStats = {
        'A': { sent: 0, approved: 0 },
        'B': { sent: 0, approved: 0 },
        'C': { sent: 0, approved: 0 }
    };
    
    messages.forEach(msg => {
        const variant = msg.variant || 'A';
        if (variantStats[variant]) {
            variantStats[variant].sent++;
            if (msg.status === 'approved' || msg.status === 'sent') {
                variantStats[variant].approved++;
            }
        }
    });
    
    const ctx = document.getElementById('messagePerformanceChart');
    if (charts.messagePerformance) charts.messagePerformance.destroy();
    
    charts.messagePerformance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Variant A', 'Variant B', 'Variant C'],
            datasets: [
                {
                    label: 'Total Generated',
                    data: [variantStats.A.sent, variantStats.B.sent, variantStats.C.sent],
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Approved/Sent',
                    data: [variantStats.A.approved, variantStats.B.approved, variantStats.C.approved],
                    backgroundColor: 'rgba(26, 188, 156, 0.7)',
                    borderColor: 'rgba(26, 188, 156, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function renderScheduleTimeline(stats) {
    const ctx = document.getElementById('scheduleTimelineChart');
    if (!ctx) return;
    
    if (charts.scheduleTimeline) charts.scheduleTimeline.destroy();
    
    charts.scheduleTimeline = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Scheduled', 'Sent Today', 'Failed'],
            datasets: [{
                label: 'Message Schedule Status',
                data: [stats.scheduled || 0, stats.sent_today || 0, stats.failed || 0],
                backgroundColor: [
                    'rgba(241, 196, 15, 0.7)',
                    'rgba(26, 188, 156, 0.7)',
                    'rgba(231, 76, 60, 0.7)'
                ],
                borderColor: [
                    'rgba(241, 196, 15, 1)',
                    'rgba(26, 188, 156, 1)',
                    'rgba(231, 76, 60, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

function showError(message) {
    alert(message);
}

// Export functionality
document.getElementById('exportBtn')?.addEventListener('click', async function() {
    try {
        const response = await fetch('/api/analytics/export');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (error) {
        console.error('Export failed:', error);
        showError('Export failed');
    }
});

// Refresh button
document.getElementById('refreshBtn')?.addEventListener('click', function() {
    loadAnalytics();
});
// A/B Test Winner Detection UI
// Add to analytics.js or create separate file

// Add Winner Detection Section to Analytics Page
function renderWinnerDetection() {
    const section = `
    <div class="bg-white rounded-lg shadow p-6 mb-8">
        <div class="flex justify-between items-center mb-4">
            <div>
                <h2 class="text-lg font-semibold text-gray-800">A/B Test Winner Detection</h2>
                <p class="text-sm text-gray-600">Automatically detect winning message variants</p>
            </div>
            <button onclick="autoAnalyzeTests()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center">
                <i data-feather="zap" class="w-4 h-4 mr-2"></i>
                Auto-Analyze All Tests
            </button>
        </div>
        
        <div id="winnerResults"></div>
        <div id="bestPractices" class="mt-6"></div>
    </div>
    `;
    
    return section;
}

// Auto-analyze all active tests
async function autoAnalyzeTests() {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i data-feather="loader" class="w-4 h-4 animate-spin mr-2"></i> Analyzing...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/ab-tests/auto-analyze', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            if (data.winners_declared > 0) {
                alert(`🏆 Declared ${data.winners_declared} winner(s)!`);
            } else {
                alert('✅ Analysis complete. No winners declared yet (need more data).');
            }
            
            // Reload winners
            loadWinners();
            loadBestPractices();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to analyze tests');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        feather.replace();
    }
}

// Load all winners
async function loadWinners() {
    try {
        const response = await fetch('/api/ab-tests/winners');
        const data = await response.json();
        
        if (data.success && data.winners.length > 0) {
            const html = `
            <div class="space-y-4">
                <h3 class="font-semibold text-gray-700 mb-3">🏆 Declared Winners</h3>
                ${data.winners.map(test => `
                    <div class="border border-green-200 bg-green-50 rounded-lg p-4">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <h4 class="font-semibold text-green-900">${test.test_name}</h4>
                                <p class="text-sm text-green-700">
                                    Winner: <span class="font-bold">Variant ${test.winning_variant}</span>
                                </p>
                            </div>
                            <span class="bg-green-600 text-white px-3 py-1 rounded-full text-xs font-semibold">
                                ${(test.confidence_level * 100).toFixed(0)}% Confidence
                            </span>
                        </div>
                        
                        <div class="grid grid-cols-3 gap-4 mt-3 text-sm">
                            <div>
                                <p class="text-gray-600">Variant A</p>
                                <p class="font-semibold">${test.variant_a_replies}/${test.variant_a_sent}</p>
                                <p class="text-xs text-gray-500">${((test.variant_a_replies/test.variant_a_sent)*100).toFixed(1)}%</p>
                            </div>
                            <div>
                                <p class="text-gray-600">Variant B</p>
                                <p class="font-semibold">${test.variant_b_replies}/${test.variant_b_sent}</p>
                                <p class="text-xs text-gray-500">${((test.variant_b_replies/test.variant_b_sent)*100).toFixed(1)}%</p>
                            </div>
                            <div>
                                <p class="text-gray-600">Variant C</p>
                                <p class="font-semibold">${test.variant_c_replies}/${test.variant_c_sent}</p>
                                <p class="text-xs text-gray-500">${((test.variant_c_replies/test.variant_c_sent)*100).toFixed(1)}%</p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            `;
            
            document.getElementById('winnerResults').innerHTML = html;
        } else {
            document.getElementById('winnerResults').innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i data-feather="award" class="w-12 h-12 mx-auto mb-2"></i>
                    <p>No winners declared yet. Continue testing!</p>
                </div>
            `;
        }
        
        feather.replace();
        
    } catch (error) {
        console.error('Error loading winners:', error);
    }
}

// Load best practices
async function loadBestPractices() {
    try {
        const response = await fetch('/api/ab-tests/best-practices');
        const data = await response.json();
        
        if (data.success && data.best_practices.total_tests > 0) {
            const practices = data.best_practices;
            
            const html = `
            <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 class="font-semibold text-purple-900 mb-3">
                    <i data-feather="trending-up" class="w-5 h-5 inline mr-1"></i>
                    Best Practices (${practices.total_tests} tests analyzed)
                </h3>
                
                <div class="grid grid-cols-3 gap-4 mb-3">
                    <div class="text-center">
                        <p class="text-sm text-purple-700">Variant A Wins</p>
                        <p class="text-2xl font-bold text-purple-900">${practices.win_rates.A.toFixed(0)}%</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-purple-700">Variant B Wins</p>
                        <p class="text-2xl font-bold text-purple-900">${practices.win_rates.B.toFixed(0)}%</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-purple-700">Variant C Wins</p>
                        <p class="text-2xl font-bold text-purple-900">${practices.win_rates.C.toFixed(0)}%</p>
                    </div>
                </div>
                
                <p class="text-sm text-purple-800">
                    <strong>💡 Recommendation:</strong> ${practices.recommendation}
                </p>
            </div>
            `;
            
            document.getElementById('bestPractices').innerHTML = html;
        }
        
        feather.replace();
        
    } catch (error) {
        console.error('Error loading best practices:', error);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('analytics')) {
        loadWinners();
        loadBestPractices();
    }
});