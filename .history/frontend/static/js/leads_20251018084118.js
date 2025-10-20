// Leads Page JavaScript - WITH APPROVE & REDIRECT FLOW
let allLeads = [];
let selectedLeadIds = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('Leads page loaded');
    loadLeads();
    loadStats();
    setupEventListeners();
});

function setupEventListeners() {
    // Filters
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }
    
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', resetFilters);
    }
    
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            toggleAllLeads(this);
        });
    }
    
    // Action buttons - CHANGED TO approve-leads-btn
    const approveBtn = document.getElementById('approve-leads-btn');
    if (approveBtn) {
        approveBtn.addEventListener('click', approveSelectedLeads);
        console.log('✅ Approve button listener attached');
    }
    
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportCSV);
    }
    
    const deleteBtn = document.getElementById('delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', deleteSelected);
    }
    
    const archiveBtn = document.getElementById('archive-btn');
    if (archiveBtn) {
        archiveBtn.addEventListener('click', archiveSelected);
    }
}

// ============================================================================
// APPROVE SELECTED LEADS & REDIRECT TO MESSAGES
// ============================================================================

function approveSelectedLeads() {
    if (selectedLeadIds.length === 0) {
        alert('Please select at least one lead first!');
        return;
    }
    
    console.log(`Approving ${selectedLeadIds.length} leads:`, selectedLeadIds);
    
    // Store selected lead IDs in sessionStorage
    sessionStorage.setItem('selected_lead_ids', JSON.stringify(selectedLeadIds));
    
    // Redirect to messages page with approval flag
    window.location.href = '/messages?approve=true';
}

// ============================================================================
// CHECKBOX SELECTION
// ============================================================================

function toggleLeadSelection(leadId, checkbox) {
    if (checkbox.checked) {
        if (!selectedLeadIds.includes(leadId)) {
            selectedLeadIds.push(leadId);
        }
    } else {
        selectedLeadIds = selectedLeadIds.filter(id => id !== leadId);
    }
    
    updateSelectionUI();
    console.log('Selected leads:', selectedLeadIds);
}

function toggleAllLeads(masterCheckbox) {
    const checkboxes = document.querySelectorAll('.lead-checkbox');
    
    if (masterCheckbox.checked) {
        selectedLeadIds = [];
        checkboxes.forEach(cb => {
            cb.checked = true;
            const leadId = parseInt(cb.dataset.leadId);
            if (!selectedLeadIds.includes(leadId)) {
                selectedLeadIds.push(leadId);
            }
        });
    } else {
        selectedLeadIds = [];
        checkboxes.forEach(cb => cb.checked = false);
    }
    
    updateSelectionUI();
    console.log('Selected leads:', selectedLeadIds);
}

function updateSelectionUI() {
    const approveBtn = document.getElementById('approve-leads-btn');
    const deleteBtn = document.getElementById('delete-btn');
    const archiveBtn = document.getElementById('archive-btn');
    
    const count = selectedLeadIds.length;
    const isSelected = count > 0;
    
    if (approveBtn) {
        approveBtn.disabled = !isSelected;
        if (isSelected) {
            approveBtn.innerHTML = `
                <i data-feather="check-circle" class="w-4 h-4 mr-2"></i>
                Approve ${count} Lead${count !== 1 ? 's' : ''}
            `;
            feather.replace();
        } else {
            approveBtn.innerHTML = `
                <i data-feather="check-circle" class="w-4 h-4 mr-2"></i>
                Approve Leads
            `;
            feather.replace();
        }
    }
    
    if (deleteBtn) deleteBtn.disabled = !isSelected;
    if (archiveBtn) archiveBtn.disabled = !isSelected;
}

// ============================================================================
// LOAD LEADS
// ============================================================================

async function loadLeads() {
    const tbody = document.getElementById('leadsTableBody');
    
    if (!tbody) {
        console.error('Table body not found');
        return;
    }
    
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                <div class="flex flex-col items-center">
                    <i data-feather="loader" class="w-12 h-12 mb-2 text-gray-400 animate-spin"></i>
                    <p>Loading leads...</p>
                </div>
            </td>
        </tr>
    `;
    feather.replace();
    
    try {
        const statusFilter = document.getElementById('status-filter')?.value;
        const personaFilter = document.getElementById('persona-filter')?.value;
        const minScore = document.getElementById('min-score')?.value;
        const maxScore = document.getElementById('max-score')?.value;
        
        let url = '/api/leads?';
        if (statusFilter && statusFilter !== 'all') url += `status=${statusFilter}&`;
        if (personaFilter && personaFilter !== 'all') url += `persona_id=${personaFilter}&`;
        if (minScore) url += `min_score=${minScore}&`;
        if (maxScore) url += `max_score=${maxScore}&`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success && data.leads.length > 0) {
            allLeads = data.leads;
            displayLeads(data.leads);
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                        <p>No leads found. Try adjusting your filters or scrape new leads.</p>
                    </td>
                </tr>
            `;
        }
        
    } catch (error) {
        console.error('Error loading leads:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-red-500">
                    <p>Error loading leads: ${error.message}</p>
                    <button onclick="loadLeads()" class="mt-2 bg-blue-500 text-white px-4 py-2 rounded">Retry</button>
                </td>
            </tr>
        `;
    }
}

function displayLeads(leads) {
    const tbody = document.getElementById('leadsTableBody');
    
    if (!tbody) return;
    
    let html = '';
    
    leads.forEach(lead => {
        const isSelected = selectedLeadIds.includes(lead.id);
        const scoreColor = getScoreColor(lead.ai_score);
        const statusBadge = getStatusBadge(lead.status);
        
        html += `
            <tr class="hover:bg-gray-50 ${isSelected ? 'bg-blue-50' : ''}">
                <td class="px-6 py-4">
                    <input type="checkbox" 
                           class="lead-checkbox rounded border-gray-300" 
                           data-lead-id="${lead.id}"
                           ${isSelected ? 'checked' : ''}
                           onchange="toggleLeadSelection(${lead.id}, this)">
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${lead.name}</div>
                    ${lead.headline ? `<div class="text-sm text-gray-500">${lead.headline}</div>` : ''}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">${lead.title || 'N/A'}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${lead.company || 'N/A'}</td>
                <td class="px-6 py-4 text-center">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${scoreColor}">
                        ${lead.ai_score || 0}
                    </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900">${lead.persona_name || 'N/A'}</td>
                <td class="px-6 py-4">
                    ${statusBadge}
                </td>
                <td class="px-6 py-4 text-center text-sm">
                    <button onclick="viewLead(${lead.id})" class="text-blue-600 hover:text-blue-900 mr-3">
                        <i data-feather="eye" class="w-4 h-4"></i>
                    </button>
                    <button onclick="deleteLead(${lead.id})" class="text-red-600 hover:text-red-900">
                        <i data-feather="trash-2" class="w-4 h-4"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    feather.replace();
    updateSelectionUI();
}

function getScoreColor(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 70) return 'bg-blue-100 text-blue-800';
    if (score >= 50) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
}

function getStatusBadge(status) {
    const badges = {
        'new': '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">New</span>',
        'contacted': '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Contacted</span>',
        'replied': '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Replied</span>',
        'qualified': '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">Qualified</span>'
    };
    return badges[status] || badges['new'];
}

// ============================================================================
// STATS
// ============================================================================

async function loadStats() {
    try {
        const response = await fetch('/api/analytics/dashboard');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('total-leads-count').textContent = data.stats.total_leads || 0;
            document.getElementById('qualified-leads-count').textContent = data.stats.qualified_leads || 0;
            document.getElementById('contacted-leads-count').textContent = data.stats.contacted_leads || 0;
            document.getElementById('replied-leads-count').textContent = data.stats.replies_received || 0;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ============================================================================
// FILTERS
// ============================================================================

function applyFilters() {
    selectedLeadIds = [];
    const selectAll = document.getElementById('select-all');
    if (selectAll) selectAll.checked = false;
    loadLeads();
}

function resetFilters() {
    document.getElementById('status-filter').value = 'all';
    document.getElementById('persona-filter').value = 'all';
    document.getElementById('min-score').value = '';
    document.getElementById('max-score').value = '';
    applyFilters();
}

// ============================================================================
// ACTIONS
// ============================================================================

function viewLead(leadId) {
    window.location.href = `/leads/${leadId}`;
}

function deleteLead(leadId) {
    if (!confirm('Delete this lead? This cannot be undone.')) return;
    
    fetch(`/api/leads/${leadId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert('Lead deleted!');
            loadLeads();
            loadStats();
        } else {
            alert('Failed to delete lead');
        }
    })
    .catch(err => alert('Error: ' + err.message));
}

function deleteSelected() {
    if (selectedLeadIds.length === 0) {
        alert('Please select leads first');
        return;
    }
    
    if (!confirm(`Delete ${selectedLeadIds.length} selected leads? This cannot be undone.`)) return;
    
    Promise.all(
        selectedLeadIds.map(id => 
            fetch(`/api/leads/${id}`, { method: 'DELETE' }).then(r => r.json())
        )
    )
    .then(() => {
        alert('Selected leads deleted!');
        selectedLeadIds = [];
        loadLeads();
        loadStats();
    })
    .catch(err => alert('Error: ' + err.message));
}

function archiveSelected() {
    alert('Archive feature coming soon!');
}

function exportCSV() {
    alert('CSV export coming soon!');
}