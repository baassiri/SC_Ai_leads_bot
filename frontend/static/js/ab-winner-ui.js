/**
 * A/B Test Winner Detection UI
 * Handles auto-analysis and winner display for A/B testing
 */

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
                alert('Winner declared! ' + data.winners_declared + ' winner(s) found');
            } else {
                alert('Analysis complete. No winners declared yet (need more data).');
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
                <h3 class="font-semibold text-gray-700 mb-3">Declared Winners</h3>
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
                        
                        <p class="text-xs text-gray-500 mt-2">
                            Declared: ${new Date(test.completed_at).toLocaleDateString()}
                        </p>
                    </div>
                `).join('')}
            </div>
            `;
            
            document.getElementById('winnerResults').innerHTML = html;
        } else {
            document.getElementById('winnerResults').innerHTML = `
                <div class="text-center py-8 text-gray-500 border-2 border-dashed rounded-lg">
                    <div class="text-4xl mb-2">TROPHY</div>
                    <p>No winners declared yet</p>
                    <p class="text-sm mt-2">Click "Auto-Analyze All Tests" to detect winners</p>
                </div>
            `;
        }
        
        feather.replace();
        
    } catch (error) {
        console.error('Error loading winners:', error);
    }
}

// Load best practices from completed tests
async function loadBestPractices() {
    try {
        const response = await fetch('/api/ab-tests/best-practices');
        const data = await response.json();
        
        if (data.success && data.best_practices && data.best_practices.length > 0) {
            const html = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 class="font-semibold text-blue-900 mb-4 flex items-center">
                    <i data-feather="award" class="w-5 h-5 mr-2"></i>
                    Best Practices from A/B Tests
                </h3>
                <div class="space-y-3">
                    ${data.best_practices.map((practice, idx) => `
                        <div class="bg-white rounded p-3 border border-blue-100">
                            <div class="flex items-start">
                                <span class="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold mr-3 flex-shrink-0">
                                    ${idx + 1}
                                </span>
                                <div class="flex-1">
                                    <p class="text-sm text-gray-700">${practice.insight}</p>
                                    <div class="flex gap-4 mt-2 text-xs text-gray-500">
                                        <span>SUCCESS: Reply Rate: ${practice.avg_reply_rate.toFixed(1)}%</span>
                                        <span>SUCCESS: Based on ${practice.test_count} test(s)</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            `;
            
            document.getElementById('bestPractices').innerHTML = html;
        } else {
            document.getElementById('bestPractices').innerHTML = `
                <div class="text-center py-6 text-gray-500">
                    <p class="text-sm">Complete more A/B tests to unlock best practices</p>
                </div>
            `;
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

console.log('AB Winner UI loaded successfully');