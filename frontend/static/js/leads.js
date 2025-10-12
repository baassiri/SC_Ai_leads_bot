/**
 * SC AI Lead Generation System - Leads Management JavaScript
 * Handles lead table, filtering, and bulk actions
 */

// Global variables
let leadsTable = null;
let selectedLeads = [];
let currentFilters = {
    status: 'all',
    persona: 'all',
    minScore: 0,
    maxScore: 100
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeLeadsTable();
    initializeFilters();
    initializeBulkActions();
    loadLeads();
});

/**
 * Initialize DataTable
 */
function initializeLeadsTable() {
    // Check if DataTable exists
    if (!$.fn.DataTable) {
        console.error('DataTables library not loaded');
        loadBasicTable();
        return;
    }
    
    leadsTable = $('#leadsTable').DataTable({
        responsive: true,
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
        order: [[4, 'desc']], // Sort by AI Score descending
        columnDefs: [
            { orderable: false, targets: [0, 7] }, // Disable sorting for checkbox and actions
            { className: 'text-center', targets: [0, 4, 5, 6] }
        ],
        dom: '<"flex justify-between items-center mb-4"<"flex"l><"flex"f>>rt<"flex justify-between items-center mt-4"<"flex"i><"flex"p>>',
        language: {
            search: "",
            searchPlaceholder: "Search leads...",
            lengthMenu: "Show _MENU_ leads",
            info: "Showing _START_ to _END_ of _TOTAL_ leads",
            paginate: {
                previous: '←',
                next: '→'
            }
        },
        drawCallback: function() {
            // Refresh feather icons after table redraw
            if (window.feather) {
                feather.replace();
            }
        }
    });
    
    // Style the search input
    $('.dataTables_filter input').addClass('border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:border-secondary');
}

/**
 * Load leads from API
 */
async function loadLeads() {
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
            displayLeads(data.leads);
        } else {
            showNotification('Failed to load leads', 'error');
        }
    } catch (error) {
        console.error('Error loading leads:', error);
        showNotification('Error loading leads', 'error');
        
        // Load sample data as fallback
        loadSampleLeads();
    }
}

/**
 * Display leads in table
 */
function displayLeads(leads) {
    if (leadsTable) {
        // Clear existing data
        leadsTable.clear();
        
        // Add new rows
        leads.forEach(lead => {
            const row = createLeadRow(lead);
            leadsTable.row.add($(row));
        });
        
        // Redraw table
        leadsTable.draw();
    } else {
        // Fallback to basic table
        displayBasicTable(leads);
    }
    
    // Update stats
    updateLeadStats(leads);
}

/**
 * Create a lead table row
 */
function createLeadRow(lead) {
    const scoreClass = getScoreClass(lead.ai_score);
    const statusClass = getStatusClass(lead.status);
    const profileImage = `https://ui-avatars.com/api/?name=${encodeURIComponent(lead.name)}&background=3498DB&color=fff`;
    
    const row = document.createElement('tr');
    row.dataset.leadId = lead.id;
    
    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
            <input type="checkbox" class="lead-checkbox rounded border-gray-300 text-secondary focus:ring-secondary" data-lead-id="${lead.id}">
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
                <div class="flex-shrink-0 h-10 w-10">
                    <img class="h-10 w-10 rounded-full" src="${profileImage}" alt="${lead.name}">
                </div>
                <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">${lead.name}</div>
                    <div class="text-sm text-gray-500">${lead.location || 'Location not specified'}</div>
                </div>
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${lead.title || 'Title not specified'}</div>
            <div class="text-sm text-gray-500">${lead.industry || 'Medical Practice'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm text-gray-900">${lead.company || 'Company not specified'}</div>
            <div class="text-sm text-gray-500">${lead.company_size || 'Size unknown'}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${scoreClass}">${lead.ai_score}/100</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full persona-match">${lead.persona || 'Unassigned'}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusClass}">${capitalizeFirst(lead.status)}</span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            <div class="flex space-x-2">
                <button class="text-secondary hover:text-blue-500" onclick="viewLead(${lead.id})" title="View Details">
                    <i data-feather="eye" class="w-4 h-4"></i>
                </button>
                <button class="text-green-500 hover:text-green-600" onclick="messageLead(${lead.id})" title="Send Message">
                    <i data-feather="message-square" class="w-4 h-4"></i>
                </button>
                <button class="text-gray-500 hover:text-gray-600" onclick="archiveLead(${lead.id})" title="Archive">
                    <i data-feather="archive" class="w-4 h-4"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

/**
 * Get score class based on value
 */
function getScoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
}

/**
 * Get status class
 */
function getStatusClass(status) {
    const statusClasses = {
        'new': 'status-new',
        'contacted': 'status-contacted',
        'replied': 'status-replied',
        'archived': 'status-archived'
    };
    return statusClasses[status] || 'status-new';
}

/**
 * Initialize filters
 */
function initializeFilters() {
    // Status filter
    const statusFilter = document.getElementById('filter-status');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentFilters.status = this.value;
            loadLeads();
        });
    }
    
    // Persona filter
    const personaFilter = document.getElementById('filter-persona');
    if (personaFilter) {
        personaFilter.addEventListener('change', function() {
            currentFilters.persona = this.value;
            loadLeads();
        });
        
        // Load personas for filter
        loadPersonasForFilter();
    }
    
    // Score range filter
    const minScore = document.getElementById('filter-min-score');
    const maxScore = document.getElementById('filter-max-score');
    
    if (minScore) {
        minScore.addEventListener('change', function() {
            currentFilters.minScore = parseInt(this.value) || 0;
            loadLeads();
        });
    }
    
    if (maxScore) {
        maxScore.addEventListener('change', function() {
            currentFilters.maxScore = parseInt(this.value) || 100;
            loadLeads();
        });
    }
    
    // Filter button
    const filterBtn = document.getElementById('apply-filters');
    if (filterBtn) {
        filterBtn.addEventListener('click', loadLeads);
    }
    
    // Reset button
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFilters);
    }
}

/**
 * Load personas for filter dropdown
 */
async function loadPersonasForFilter() {
    try {
        const response = await fetch('/api/personas');
        const data = await response.json();
        
        if (data.success && data.personas) {
            const select = document.getElementById('filter-persona');
            if (select) {
                // Clear existing options except "All"
                select.innerHTML = '<option value="all">All Personas</option>';
                
                // Add persona options
                data.personas.forEach(persona => {
                    const option = document.createElement('option');
                    option.value = persona.id;
                    option.textContent = persona.name;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading personas:', error);
    }
}

/**
 * Reset all filters
 */
function resetFilters() {
    currentFilters = {
        status: 'all',
        persona: 'all',
        minScore: 0,
        maxScore: 100
    };
    
    // Reset form inputs
    document.getElementById('filter-status').value = 'all';
    document.getElementById('filter-persona').value = 'all';
    document.getElementById('filter-min-score').value = '';
    document.getElementById('filter-max-score').value = '';
    
    loadLeads();
}

/**
 * Initialize bulk actions
 */
function initializeBulkActions() {
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-leads');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.lead-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = this.checked;
                updateSelectedLeads(cb);
            });
            updateBulkActionUI();
        });
    }
    
    // Individual checkboxes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('lead-checkbox')) {
            updateSelectedLeads(e.target);
            updateBulkActionUI();
        }
    });
    
    // Bulk action buttons
    document.getElementById('bulk-message')?.addEventListener('click', bulkMessage);
    document.getElementById('bulk-archive')?.addEventListener('click', bulkArchive);
    document.getElementById('bulk-delete')?.addEventListener('click', bulkDelete);
    document.getElementById('bulk-export')?.addEventListener('click', exportLeads);
}

/**
 * Update selected leads array
 */
function updateSelectedLeads(checkbox) {
    const leadId = parseInt(checkbox.dataset.leadId);
    
    if (checkbox.checked) {
        if (!selectedLeads.includes(leadId)) {
            selectedLeads.push(leadId);
        }
    } else {
        selectedLeads = selectedLeads.filter(id => id !== leadId);
    }
}

/**
 * Update bulk action UI
 */
function updateBulkActionUI() {
    const selectedCount = selectedLeads.length;
    const countElement = document.getElementById('selected-count');
    
    if (countElement) {
        countElement.textContent = `${selectedCount} ${selectedCount === 1 ? 'lead' : 'leads'} selected`;
    }
    
    // Enable/disable bulk action buttons
    const bulkButtons = document.querySelectorAll('.bulk-action-btn');
    bulkButtons.forEach(btn => {
        btn.disabled = selectedCount === 0;
        btn.classList.toggle('opacity-50', selectedCount === 0);
    });
}

/**
 * View lead details
 */
async function viewLead(leadId) {
    try {
        const response = await fetch(`/api/leads/${leadId}`);
        const data = await response.json();
        
        if (data.success) {
            showLeadModal(data.lead);
        } else {
            showNotification('Failed to load lead details', 'error');
        }
    } catch (error) {
        console.error('Error loading lead:', error);
        showNotification('Error loading lead details', 'error');
    }
}

/**
 * Show lead details modal
 */
function showLeadModal(lead) {
    // Create modal HTML
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 overflow-y-auto';
    modal.innerHTML = `
        <div class="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div class="fixed inset-0 transition-opacity" onclick="closeLeadModal()">
                <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Lead Details</h3>
                            
                            <div class="space-y-3">
                                <div>
                                    <label class="text-sm font-medium text-gray-500">Name</label>
                                    <p class="text-sm text-gray-900">${lead.name}</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">Title</label>
                                    <p class="text-sm text-gray-900">${lead.title || 'Not specified'}</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">Company</label>
                                    <p class="text-sm text-gray-900">${lead.company || 'Not specified'}</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">Location</label>
                                    <p class="text-sm text-gray-900">${lead.location || 'Not specified'}</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">AI Score</label>
                                    <p class="text-sm text-gray-900">${lead.ai_score}/100</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">Score Reasoning</label>
                                    <p class="text-sm text-gray-900">${lead.score_reasoning || 'No reasoning provided'}</p>
                                </div>
                                
                                <div>
                                    <label class="text-sm font-medium text-gray-500">LinkedIn Profile</label>
                                    <a href="${lead.profile_url}" target="_blank" class="text-sm text-secondary hover:text-blue-500">View Profile →</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button type="button" onclick="messageLead(${lead.id})" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-success text-base font-medium text-white hover:bg-green-600 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">
                        Send Message
                    </button>
                    <button type="button" onclick="closeLeadModal()" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

/**
 * Close lead modal
 */
function closeLeadModal() {
    const modal = document.querySelector('.fixed.inset-0.z-50');
    if (modal) {
        modal.remove();
    }
}

/**
 * Message a lead
 */
function messageLead(leadId) {
    // Redirect to messages page with lead pre-selected
    window.location.href = `/messages?lead=${leadId}`;
}

/**
 * Archive a lead
 */
async function archiveLead(leadId) {
    if (!confirm('Are you sure you want to archive this lead?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/leads/${leadId}/archive`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Lead archived successfully', 'success');
            loadLeads(); // Reload table
        } else {
            showNotification('Failed to archive lead', 'error');
        }
    } catch (error) {
        console.error('Error archiving lead:', error);
        showNotification('Error archiving lead', 'error');
    }
}

/**
 * Bulk message selected leads
 */
async function bulkMessage() {
    if (selectedLeads.length === 0) {
        showNotification('Please select leads first', 'warning');
        return;
    }
    
    // Redirect to messages page with selected leads
    const leadIds = selectedLeads.join(',');
    window.location.href = `/messages?bulk=${leadIds}`;
}

/**
 * Bulk archive selected leads
 */
async function bulkArchive() {
    if (selectedLeads.length === 0) {
        showNotification('Please select leads first', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to archive ${selectedLeads.length} leads?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/bulk-archive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_ids: selectedLeads })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${selectedLeads.length} leads archived successfully`, 'success');
            selectedLeads = [];
            loadLeads();
        } else {
            showNotification('Failed to archive leads', 'error');
        }
    } catch (error) {
        console.error('Error archiving leads:', error);
        showNotification('Error archiving leads', 'error');
    }
}

/**
 * Bulk delete selected leads
 */
async function bulkDelete() {
    if (selectedLeads.length === 0) {
        showNotification('Please select leads first', 'warning');
        return;
    }
    
    if (!confirm(`Are you sure you want to DELETE ${selectedLeads.length} leads? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/bulk-delete', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_ids: selectedLeads })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${selectedLeads.length} leads deleted successfully`, 'success');
            selectedLeads = [];
            loadLeads();
        } else {
            showNotification('Failed to delete leads', 'error');
        }
    } catch (error) {
        console.error('Error deleting leads:', error);
        showNotification('Error deleting leads', 'error');
    }
}

/**
 * Export leads to CSV
 */
async function exportLeads() {
    try {
        const params = new URLSearchParams();
        
        // Add selected leads or current filters
        if (selectedLeads.length > 0) {
            params.append('lead_ids', selectedLeads.join(','));
        } else {
            if (currentFilters.status !== 'all') {
                params.append('status', currentFilters.status);
            }
            if (currentFilters.persona !== 'all') {
                params.append('persona_id', currentFilters.persona);
            }
            if (currentFilters.minScore > 0) {
                params.append('min_score', currentFilters.minScore);
            }
        }
        
        // Trigger download
        window.location.href = `/api/leads/export?${params.toString()}`;
        showNotification('Export started...', 'success');
        
    } catch (error) {
        console.error('Error exporting leads:', error);
        showNotification('Error exporting leads', 'error');
    }
}

/**
 * Update lead statistics
 */
function updateLeadStats(leads) {
    const statsContainer = document.getElementById('lead-stats');
    if (!statsContainer) return;
    
    const stats = {
        total: leads.length,
        qualified: leads.filter(l => l.ai_score >= 70).length,
        contacted: leads.filter(l => l.status === 'contacted').length,
        replied: leads.filter(l => l.status === 'replied').length
    };
    
    statsContainer.innerHTML = `
        <div class="flex space-x-6 text-sm text-gray-600">
            <span>Total: <strong>${stats.total}</strong></span>
            <span>Qualified: <strong>${stats.qualified}</strong></span>
            <span>Contacted: <strong>${stats.contacted}</strong></span>
            <span>Replied: <strong>${stats.replied}</strong></span>
        </div>
    `;
}

/**
 * Fallback: Display basic table without DataTables
 */
function displayBasicTable(leads) {
    const tbody = document.querySelector('#leadsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    leads.forEach(lead => {
        const row = createLeadRow(lead);
        tbody.appendChild(row);
    });
    
    // Refresh feather icons
    if (window.feather) {
        feather.replace();
    }
}

/**
 * Load sample leads for testing
 */
function loadSampleLeads() {
    const sampleLeads = [
        {
            id: 1,
            name: 'Dr. Sarah Johnson',
            title: 'Cosmetic Surgeon',
            company: 'Beverly Hills Aesthetics',
            industry: 'Medical Practice',
            location: 'Los Angeles, CA',
            ai_score: 92,
            persona: 'Plastic Surgeon',
            status: 'new'
        },
        {
            id: 2,
            name: 'Dr. Michael Chen',
            title: 'Dermatologist',
            company: 'Skin Perfect Clinic',
            industry: 'Medical Practice',
            location: 'New York, NY',
            ai_score: 87,
            persona: 'Dermatologist',
            status: 'contacted'
        },
        {
            id: 3,
            name: 'Jessica Williams',
            title: 'Aesthetic Nurse',
            company: 'Glow Med Spa',
            industry: 'Medical Practice',
            location: 'Miami, FL',
            ai_score: 76,
            persona: 'Med Spa Owner',
            status: 'replied'
        }
    ];
    
    displayLeads(sampleLeads);
}

/**
 * Utility: Capitalize first letter
 */
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    
    const typeConfig = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'info': 'bg-secondary',
        'warning': 'bg-warning'
    };
    
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${typeConfig[type]} text-white`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}