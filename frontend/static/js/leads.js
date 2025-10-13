/**
 * Leads Management - FIXED VERSION
 * Handles lead display, filtering, and actions
 */

let allLeads = [];
let currentFilters = {
    status: 'all',
    persona: 'all',
    minScore: 0,
    maxScore: 100
};

/**
 * Initialize page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Leads page...');
    
    // Load leads immediately
    loadLeads();
    
    // Setup filter handlers
    setupFilters();
    
    // Setup action buttons
    setupActionButtons();
    
    // Replace feather icons
    if (window.feather) {
        feather.replace();
    }
});

/**
 * Load leads from API
 */
async function loadLeads() {
    console.log('📥 Loading leads from API...');
    
    try {
        // Build query parameters
        const params = new URLSearchParams();
        if (currentFilters.status !== 'all') {
            params.append('status', currentFilters.status);
        }
        if (currentFilters.persona !== 'all') {
            params.append('persona_id', currentFilters.persona);
        }
        if (currentFilters.minScore > 0) {
            params.append('min_score', currentFilters.minScore);
        }
        
        const response = await fetch(`/api/leads?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Loaded ${data.leads.length} leads`);
            allLeads = data.leads;
            displayLeads(data.leads);
        } else {
            console.error('❌ Failed to load leads:', data.message);
            showError('Failed to load leads: ' + data.message);
        }
    } catch (error) {
        console.error('❌ Error loading leads:', error);
        showError('Error loading leads. Check console for details.');
    }
}

/**
 * Display leads in table
 */
function displayLeads(leads) {
    console.log(`📊 Displaying ${leads.length} leads...`);
    
    const tbody = document.getElementById('leadsTableBody');
    
    if (!tbody) {
        console.error('❌ Table body not found!');
        return;
    }
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    <i data-feather="inbox" class="w-12 h-12 mx-auto mb-2 text-gray-400"></i>
                    <p>No leads found. Try adjusting your filters or start scraping!</p>
                </td>
            </tr>
        `;
        if (window.feather) feather.replace();
        return;
    }
    
    // Add each lead as a row
    leads.forEach(lead => {
        const row = createLeadRow(lead);
        tbody.appendChild(row);
    });
    
    // Replace feather icons
    if (window.feather) {
        feather.replace();
    }
    
    console.log('✅ Leads displayed successfully');
}

/**
 * Create a lead table row
 */
function createLeadRow(lead) {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50';
    row.dataset.leadId = lead.id;
    
    // Score badge color
    const scoreColor = lead.ai_score >= 80 ? 'bg-green-100 text-green-800' :
                      lead.ai_score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800';
    
    // Status badge color
    const statusColors = {
        'new': 'bg-blue-100 text-blue-800',
        'contacted': 'bg-purple-100 text-purple-800',
        'replied': 'bg-green-100 text-green-800',
        'qualified': 'bg-yellow-100 text-yellow-800'
    };
    const statusColor = statusColors[lead.status] || 'bg-gray-100 text-gray-800';
    
    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
            <input type="checkbox" class="lead-checkbox rounded border-gray-300" data-lead-id="${lead.id}">
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-medium text-gray-900">${lead.name || 'Unknown'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${lead.title || 'N/A'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${lead.company || 'N/A'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-center">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${scoreColor}">
                ${lead.ai_score || 0}/100
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${lead.persona_name || 'N/A'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}">
                ${(lead.status || 'new').charAt(0).toUpperCase() + (lead.status || 'new').slice(1)}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <button onclick="viewLead(${lead.id})" class="text-indigo-600 hover:text-indigo-900 mr-3" title="View Details">
                <i data-feather="eye" class="w-4 h-4"></i>
            </button>
            <button onclick="generateMessages(${lead.id})" class="text-green-600 hover:text-green-900" title="Generate Message">
                <i data-feather="message-circle" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    
    return row;
}

/**
 * Setup filter handlers
 */
function setupFilters() {
    // Status filter
    const statusSelect = document.getElementById('status-filter');
    if (statusSelect) {
        statusSelect.addEventListener('change', (e) => {
            currentFilters.status = e.target.value;
            loadLeads();
        });
    }
    
    // Persona filter
    const personaSelect = document.getElementById('persona-filter');
    if (personaSelect) {
        personaSelect.addEventListener('change', (e) => {
            currentFilters.persona = e.target.value;
            loadLeads();
        });
    }
    
    // Score filters
    const minScoreInput = document.getElementById('min-score');
    const maxScoreInput = document.getElementById('max-score');
    
    if (minScoreInput) {
        minScoreInput.addEventListener('change', (e) => {
            currentFilters.minScore = parseInt(e.target.value) || 0;
            loadLeads();
        });
    }
    
    if (maxScoreInput) {
        maxScoreInput.addEventListener('change', (e) => {
            currentFilters.maxScore = parseInt(e.target.value) || 100;
            loadLeads();
        });
    }
    
    // Apply filters button
    const applyBtn = document.getElementById('apply-filters');
    if (applyBtn) {
        applyBtn.addEventListener('click', loadLeads);
    }
    
    // Reset filters button
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentFilters = {
                status: 'all',
                persona: 'all',
                minScore: 0,
                maxScore: 100
            };
            
            if (statusSelect) statusSelect.value = 'all';
            if (personaSelect) personaSelect.value = 'all';
            if (minScoreInput) minScoreInput.value = '';
            if (maxScoreInput) maxScoreInput.value = '';
            
            loadLeads();
        });
    }
}

/**
 * Setup action buttons
 */
function setupActionButtons() {
    // Generate Messages button
    const generateBtn = document.getElementById('generate-messages-btn');
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            const selectedLeads = getSelectedLeads();
            
            if (selectedLeads.length === 0) {
                alert('Please select at least one lead');
                return;
            }
            
            if (confirm(`Generate messages for ${selectedLeads.length} selected lead(s)?`)) {
                await generateMessagesForLeads(selectedLeads);
            }
        });
    }
    
    // Archive button
    const archiveBtn = document.getElementById('archive-btn');
    if (archiveBtn) {
        archiveBtn.addEventListener('click', async () => {
            const selectedLeads = getSelectedLeads();
            
            if (selectedLeads.length === 0) {
                alert('Please select at least one lead');
                return;
            }
            
            if (confirm(`Archive ${selectedLeads.length} selected lead(s)?`)) {
                await archiveLeads(selectedLeads);
            }
        });
    }
    
    // Delete button
    const deleteBtn = document.getElementById('delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', async () => {
            const selectedLeads = getSelectedLeads();
            
            if (selectedLeads.length === 0) {
                alert('Please select at least one lead');
                return;
            }
            
            if (confirm(`Delete ${selectedLeads.length} selected lead(s)? This cannot be undone.`)) {
                await deleteLeads(selectedLeads);
            }
        });
    }
    
    // Export CSV button
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }
}

/**
 * Get selected lead IDs
 */
function getSelectedLeads() {
    const checkboxes = document.querySelectorAll('.lead-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.dataset.leadId));
}

/**
 * View lead details
 */
function viewLead(leadId) {
    window.location.href = `/leads/${leadId}`;
}

/**
 * Generate messages for a single lead
 */
async function generateMessages(leadId) {
    try {
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_ids: [leadId] })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Messages generated successfully!');
            window.location.href = '/messages';
        } else {
            alert('❌ Failed to generate messages: ' + data.message);
        }
    } catch (error) {
        console.error('Error generating messages:', error);
        alert('❌ Error generating messages');
    }
}

/**
 * Generate messages for multiple leads
 */
async function generateMessagesForLeads(leadIds) {
    try {
        const response = await fetch('/api/messages/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_ids: leadIds })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`✅ Generated ${data.results.messages_created} messages for ${data.results.successful} leads!`);
            window.location.href = '/messages';
        } else {
            alert('❌ Failed to generate messages: ' + data.message);
        }
    } catch (error) {
        console.error('Error generating messages:', error);
        alert('❌ Error generating messages');
    }
}

/**
 * Archive leads
 */
async function archiveLeads(leadIds) {
    // TODO: Implement archive functionality
    alert('Archive functionality coming soon!');
}

/**
 * Delete leads
 */
async function deleteLeads(leadIds) {
    // TODO: Implement delete functionality
    alert('Delete functionality coming soon!');
}

/**
 * Export leads to CSV
 */
function exportToCSV() {
    if (allLeads.length === 0) {
        alert('No leads to export');
        return;
    }
    
    // Create CSV content
    const headers = ['Name', 'Title', 'Company', 'Industry', 'Location', 'AI Score', 'Persona', 'Status'];
    const rows = allLeads.map(lead => [
        lead.name || '',
        lead.title || '',
        lead.company || '',
        lead.industry || '',
        lead.location || '',
        lead.ai_score || 0,
        lead.persona_name || '',
        lead.status || 'new'
    ]);
    
    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
    });
    
    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    console.log('✅ Exported leads to CSV');
}

/**
 * Show error message
 */
function showError(message) {
    const tbody = document.getElementById('leadsTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-red-500">
                    <i data-feather="alert-circle" class="w-12 h-12 mx-auto mb-2"></i>
                    <p>${message}</p>
                </td>
            </tr>
        `;
        if (window.feather) feather.replace();
    }
}

console.log('✅ Leads.js loaded successfully');