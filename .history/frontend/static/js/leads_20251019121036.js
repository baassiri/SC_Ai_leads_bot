// leads.js - Lead management functionality with timeline integration

let allLeads = [];
let filteredLeads = [];
let currentPage = 1;
const leadsPerPage = 25;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadLeads();
    setupEventListeners();
    feather.replace(); // Initialize feather icons
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    document.getElementById('select-all').addEventListener('change', toggleSelectAll);
    document.getElementById('approve-leads-btn').addEventListener('click', approveSelectedLeads);
    document.getElementById('archive-btn').addEventListener('click', archiveSelectedLeads);
    document.getElementById('delete-btn').addEventListener('click', deleteSelectedLeads);
    document.getElementById('export-csv-btn').addEventListener('click', exportLeads);
}

// Load leads from API
async function loadLeads() {
    try {
        showLoading();
        const response = await fetch('/api/leads');
        const data = await response.json();
        
        if (data.success) {
            allLeads = data.leads;
            filteredLeads = allLeads;
            updateStats();
            renderLeads();
            loadPersonaFilter();
        } else {
            showError('Failed to load leads: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading leads:', error);
        showError('Failed to load leads. Please refresh the page.');
    }
}

// Update statistics
function updateStats() {
    const totalLeads = allLeads.length;
    const qualifiedLeads = allLeads.filter(lead => lead.ai_score >= 70).length;
    const contactedLeads = allLeads.filter(lead => lead.status === 'contacted').length;
    const repliedLeads = allLeads.filter(lead => lead.status === 'replied').length;
    
    document.getElementById('total-leads-count').textContent = totalLeads;
    document.getElementById('qualified-leads-count').textContent = qualifiedLeads;
    document.getElementById('contacted-leads-count').textContent = contactedLeads;
    document.getElementById('replied-leads-count').textContent = repliedLeads;
}

// Render leads table
function renderLeads() {
    const tbody = document.getElementById('leadsTableBody');
    const start = (currentPage - 1) * leadsPerPage;
    const end = start + leadsPerPage;
    const pageLeads = filteredLeads.slice(start, end);
    
    if (pageLeads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <i data-feather="inbox" class="w-12 h-12 mb-2 text-gray-400"></i>
                        <p>No leads found</p>
                    </div>
                </td>
            </tr>
        `;
        feather.replace();
        return;
    }
    
    tbody.innerHTML = pageLeads.map(lead => `
        <tr class="hover:bg-gray-50">
            <td class="px-6 py-4">
                <input type="checkbox" class="lead-checkbox rounded border-gray-300" value="${lead.id}">
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-10">
                        <div class="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                            ${getInitials(lead.name)}
                        </div>
                    </div>
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${escapeHtml(lead.name)}</div>
                        <div class="text-sm text-gray-500">${escapeHtml(lead.email || '')}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(lead.title || 'N/A')}</td>
            <td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(lead.company || 'N/A')}</td>
            <td class="px-6 py-4 text-center">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreBadgeClass(lead.ai_score)}">
                    ${lead.ai_score || 0}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-900">${escapeHtml(lead.persona || 'N/A')}</td>
            <td class="px-6 py-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(lead.status)}">
                    ${formatStatus(lead.status)}
                </span>
            </td>
            <td class="px-6 py-4 text-center">
                <div class="flex items-center justify-center space-x-2">
                    <button onclick="showTimeline(${lead.id}, '${escapeHtml(lead.name).replace(/'/g, "\\'")}')" 
                            class="text-gray-600 hover:text-blue-600 p-1 rounded hover:bg-gray-100" 
                            title="View Timeline">
                        <i data-feather="clock" class="w-4 h-4"></i>
                    </button>
                    <button onclick="viewLead(${lead.id})" 
                            class="text-gray-600 hover:text-blue-600 p-1 rounded hover:bg-gray-100" 
                            title="View Details">
                        <i data-feather="eye" class="w-4 h-4"></i>
                    </button>
                    <button onclick="editLead(${lead.id})" 
                            class="text-gray-600 hover:text-green-600 p-1 rounded hover:bg-gray-100" 
                            title="Edit Lead">
                        <i data-feather="edit-2" class="w-4 h-4"></i>
                    </button>
                    <button onclick="sendMessage(${lead.id})" 
                            class="text-gray-600 hover:text-purple-600 p-1 rounded hover:bg-gray-100" 
                            title="Send Message">
                        <i data-feather="message-circle" class="w-4 h-4"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
    
    feather.replace();
    updatePagination();
}

// Apply filters
function applyFilters() {
    const status = document.getElementById('status-filter').value;
    const persona = document.getElementById('persona-filter').value;
    const minScore = parseInt(document.getElementById('min-score').value) || 0;
    const maxScore = parseInt(document.getElementById('max-score').value) || 100;
    
    filteredLeads = allLeads.filter(lead => {
        let matches = true;
        
        if (status !== 'all' && lead.status !== status) {
            matches = false;
        }
        
        if (persona !== 'all' && lead.persona !== persona) {
            matches = false;
        }
        
        const score = lead.ai_score || 0;
        if (score < minScore || score > maxScore) {
            matches = false;
        }
        
        return matches;
    });
    
    currentPage = 1;
    renderLeads();
}

// Reset filters
function resetFilters() {
    document.getElementById('status-filter').value = 'all';
    document.getElementById('persona-filter').value = 'all';
    document.getElementById('min-score').value = '';
    document.getElementById('max-score').value = '';
    
    filteredLeads = allLeads;
    currentPage = 1;
    renderLeads();
}

// Load persona filter options
function loadPersonaFilter() {
    const personas = [...new Set(allLeads.map(lead => lead.persona).filter(p => p))];
    const select = document.getElementById('persona-filter');
    
    personas.forEach(persona => {
        const option = document.createElement('option');
        option.value = persona;
        option.textContent = persona;
        select.appendChild(option);
    });
}

// Toggle select all
function toggleSelectAll() {
    const isChecked = document.getElementById('select-all').checked;
    document.querySelectorAll('.lead-checkbox').forEach(checkbox => {
        checkbox.checked = isChecked;
    });
}

// Get selected lead IDs
function getSelectedLeadIds() {
    return Array.from(document.querySelectorAll('.lead-checkbox:checked'))
        .map(cb => parseInt(cb.value));
}

// Approve selected leads
async function approveSelectedLeads() {
    const leadIds = getSelectedLeadIds();
    
    if (leadIds.length === 0) {
        showNotification('Please select leads to approve', 'warning');
        return;
    }
    
    if (!confirm(`Approve ${leadIds.length} lead(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/bulk-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lead_ids: leadIds,
                updates: { status: 'qualified' }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Leads approved successfully', 'success');
            loadLeads();
        } else {
            showNotification('Failed to approve leads: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error approving leads:', error);
        showNotification('Failed to approve leads', 'error');
    }
}

// Archive selected leads
async function archiveSelectedLeads() {
    const leadIds = getSelectedLeadIds();
    
    if (leadIds.length === 0) {
        showNotification('Please select leads to archive', 'warning');
        return;
    }
    
    if (!confirm(`Archive ${leadIds.length} lead(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/bulk-update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lead_ids: leadIds,
                updates: { status: 'archived' }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Leads archived successfully', 'success');
            loadLeads();
        } else {
            showNotification('Failed to archive leads: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error archiving leads:', error);
        showNotification('Failed to archive leads', 'error');
    }
}

// Delete selected leads
async function deleteSelectedLeads() {
    const leadIds = getSelectedLeadIds();
    
    if (leadIds.length === 0) {
        showNotification('Please select leads to delete', 'warning');
        return;
    }
    
    if (!confirm(`Delete ${leadIds.length} lead(s)? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const deletePromises = leadIds.map(id => 
            fetch(`/api/leads/${id}`, { method: 'DELETE' })
        );
        
        await Promise.all(deletePromises);
        
        showNotification('Leads deleted successfully', 'success');
        loadLeads();
    } catch (error) {
        console.error('Error deleting leads:', error);
        showNotification('Failed to delete leads', 'error');
    }
}

// Export leads to CSV
function exportLeads() {
    window.location.href = '/api/leads/export';
}

// View lead details
function viewLead(leadId) {
    window.location.href = `/leads/${leadId}`;
}

// Edit lead
function editLead(leadId) {
    window.location.href = `/leads/${leadId}/edit`;
}

// Send message to lead
function sendMessage(leadId) {
    window.location.href = `/messages/compose?lead_id=${leadId}`;
}

// Update pagination
function updatePagination() {
    const totalPages = Math.ceil(filteredLeads.length / leadsPerPage);
    // Add pagination UI if needed
}

// Helper functions
function getInitials(name) {
    if (!name) return '?';
    return name.split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getScoreBadgeClass(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 70) return 'bg-blue-100 text-blue-800';
    if (score >= 50) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
}

function getStatusBadgeClass(status) {
    const classes = {
        'new': 'bg-blue-100 text-blue-800',
        'contacted': 'bg-yellow-100 text-yellow-800',
        'replied': 'bg-purple-100 text-purple-800',
        'qualified': 'bg-green-100 text-green-800',
        'archived': 'bg-gray-100 text-gray-800'
    };
    return classes[status] || 'bg-gray-100 text-gray-800';
}

function formatStatus(status) {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
}

function showLoading() {
    const tbody = document.getElementById('leadsTableBody');
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
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // You can implement a toast notification system here
    // For now, using alert
    alert(message);
}