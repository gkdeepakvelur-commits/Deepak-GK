/**
 * Enhanced Student Result Management System
 * Advanced JavaScript Functions for Bulk Operations and Analytics
 */

// Enhanced application initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeEnhancedFeatures();
});

function initializeEnhancedFeatures() {
    initializeBulkOperations();
    initializeAdvancedSearch();
    initializeExportFeatures();
    initializeProgressTracking();
    initializeNotifications();
    initializeDataVisualization();
    initializeFormEnhancements();
    
    console.log('Enhanced SRMS features initialized');
}

// Bulk Operations Management
function initializeBulkOperations() {
    // CSV file upload with drag and drop
    const uploadZones = document.querySelectorAll('.csv-upload-zone');
    uploadZones.forEach(zone => {
        setupAdvancedFileUpload(zone);
    });
    
    // Bulk operation progress tracking
    initializeBulkProgressTracking();
    
    // CSV validation and preview
    initializeCSVValidation();
}

function setupAdvancedFileUpload(zone) {
    const fileInput = zone.querySelector('input[type="file"]');
    
    // Drag and drop events
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    
    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelection(files[0], zone);
        }
    });
    
    // Click to upload
    zone.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0], zone);
        }
    });
}

function handleFileSelection(file, zone) {
    // Validate file
    if (!file.name.endsWith('.csv')) {
        showNotification('Please select a CSV file', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showNotification('File size must be less than 10MB', 'error');
        return;
    }
    
    // Show file preview
    showFilePreview(file, zone);
    
    // Parse and validate CSV
    parseCSVFile(file).then(data => {
        showCSVPreview(data, zone);
    }).catch(error => {
        showNotification(`Error parsing CSV: ${error.message}`, 'error');
    });
}

function showFilePreview(file, zone) {
    const previewContainer = zone.querySelector('.file-preview') || createFilePreviewContainer(zone);
    
    previewContainer.innerHTML = `
        <div class="file-preview-item">
            <i class="fas fa-file-csv file-icon"></i>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFilePreview(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
}

function createFilePreviewContainer(zone) {
    const container = document.createElement('div');
    container.className = 'file-preview-container';
    zone.appendChild(container);
    return container;
}

function removeFilePreview(button) {
    const previewItem = button.closest('.file-preview-item');
    const zone = button.closest('.csv-upload-zone');
    const fileInput = zone.querySelector('input[type="file"]');
    
    previewItem.remove();
    fileInput.value = '';
}

function parseCSVFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const csv = e.target.result;
                const lines = csv.split('\n');
                const headers = lines[0].split(',').map(h => h.trim());
                const data = [];
                
                for (let i = 1; i < lines.length; i++) {
                    if (lines[i].trim()) {
                        const values = lines[i].split(',').map(v => v.trim());
                        const row = {};
                        headers.forEach((header, index) => {
                            row[header] = values[index] || '';
                        });
                        data.push(row);
                    }
                }
                
                resolve({ headers, data });
            } catch (error) {
                reject(error);
            }
        };
        reader.onerror = reject;
        reader.readAsText(file);
    });
}

function showCSVPreview(csvData, zone) {
    const previewContainer = zone.querySelector('.csv-preview') || createCSVPreviewContainer(zone);
    
    // Validate headers based on operation type
    const operationType = zone.closest('form').querySelector('input[name="operation"]').value;
    const validation = validateCSVHeaders(csvData.headers, operationType);
    
    let previewHTML = `
        <div class="csv-preview-header">
            <h6>CSV Preview (${csvData.data.length} records)</h6>
        </div>
    `;
    
    if (!validation.valid) {
        previewHTML += `
            <div class="alert alert-warning">
                <strong>Header validation issues:</strong><br>
                ${validation.issues.join('<br>')}
            </div>
        `;
    }
    
    // Show first 5 rows
    const previewRows = csvData.data.slice(0, 5);
    previewHTML += `
        <div class="table-responsive">
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        ${csvData.headers.map(h => `<th>${h}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${previewRows.map(row => `
                        <tr>
                            ${csvData.headers.map(h => `<td>${row[h] || ''}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    if (csvData.data.length > 5) {
        previewHTML += `<small class="text-muted">... and ${csvData.data.length - 5} more records</small>`;
    }
    
    previewContainer.innerHTML = previewHTML;
}

function createCSVPreviewContainer(zone) {
    const container = document.createElement('div');
    container.className = 'csv-preview mt-3';
    zone.appendChild(container);
    return container;
}

function validateCSVHeaders(headers, operationType) {
    const expectedHeaders = {
        'import_students': ['roll_no', 'name', 'email', 'phone', 'date_of_birth', 'department', 'semester', 'admission_year', 'address'],
        'import_marks': ['roll_no', 'subject_code', 'marks_obtained', 'total_marks', 'exam_type', 'exam_date']
    };
    
    const required = expectedHeaders[operationType] || [];
    const missing = required.filter(h => !headers.includes(h));
    const extra = headers.filter(h => !required.includes(h));
    
    return {
        valid: missing.length === 0,
        issues: [
            ...missing.map(h => `Missing required header: ${h}`),
            ...extra.map(h => `Unexpected header: ${h}`)
        ]
    };
}

// Progress Tracking for Bulk Operations
function initializeBulkProgressTracking() {
    const progressElements = document.querySelectorAll('.bulk-progress');
    progressElements.forEach(element => {
        const operationId = element.dataset.operationId;
        if (operationId) {
            trackBulkOperation(operationId, element);
        }
    });
}

function trackBulkOperation(operationId, element) {
    const checkProgress = () => {
        fetch(`/api/bulk-operation/${operationId}/status`)
            .then(response => response.json())
            .then(data => {
                updateProgressDisplay(data, element);
                
                if (data.status === 'pending' || data.status === 'processing') {
                    setTimeout(checkProgress, 2000); // Check every 2 seconds
                }
            })
            .catch(error => {
                console.error('Error checking progress:', error);
            });
    };
    
    checkProgress();
}

function updateProgressDisplay(operationData, element) {
    const percentage = operationData.total_records > 0 
        ? Math.round((operationData.processed_records / operationData.total_records) * 100)
        : 0;
    
    element.innerHTML = `
        <div class="progress mb-2">
            <div class="progress-bar" style="width: ${percentage}%"></div>
        </div>
        <div class="d-flex justify-content-between text-sm">
            <span>${operationData.processed_records}/${operationData.total_records} processed</span>
            <span class="badge bg-${getStatusColor(operationData.status)}">${operationData.status}</span>
        </div>
        ${operationData.failed_records > 0 ? `
            <div class="text-danger mt-1">
                <small>${operationData.failed_records} failed</small>
            </div>
        ` : ''}
    `;
}

function getStatusColor(status) {
    const colors = {
        'pending': 'warning',
        'processing': 'info',
        'completed': 'success',
        'failed': 'danger'
    };
    return colors[status] || 'secondary';
}

// Advanced Search Features
function initializeAdvancedSearch() {
    const searchInputs = document.querySelectorAll('.advanced-search');
    searchInputs.forEach(input => {
        setupAdvancedSearch(input);
    });
}

function setupAdvancedSearch(input) {
    let searchTimeout;
    const suggestionsContainer = createSuggestionsContainer(input);
    
    input.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            hideSuggestions(suggestionsContainer);
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performAdvancedSearch(query, suggestionsContainer);
        }, 300);
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            hideSuggestions(suggestionsContainer);
        }
    });
}

function createSuggestionsContainer(input) {
    const container = document.createElement('div');
    container.className = 'search-suggestions';
    container.style.display = 'none';
    input.parentNode.appendChild(container);
    return container;
}

function performAdvancedSearch(query, container) {
    // This would typically make an API call to search for students/subjects
    // For now, we'll simulate with localStorage or show a "searching..." message
    container.innerHTML = '<div class="search-suggestion-item">Searching...</div>';
    container.style.display = 'block';
    
    // Simulate API delay
    setTimeout(() => {
        const suggestions = getSearchSuggestions(query);
        displaySearchSuggestions(suggestions, container);
    }, 500);
}

function getSearchSuggestions(query) {
    // This would typically come from an API
    // For demo purposes, return some mock suggestions
    return [
        { type: 'student', value: `${query}001`, label: `Student ${query}001 - John Doe` },
        { type: 'student', value: `${query}002`, label: `Student ${query}002 - Jane Smith` },
        { type: 'subject', value: `CS${query}`, label: `Subject CS${query} - Computer Science` }
    ].filter(item => item.label.toLowerCase().includes(query.toLowerCase()));
}

function displaySearchSuggestions(suggestions, container) {
    if (suggestions.length === 0) {
        container.innerHTML = '<div class="search-suggestion-item text-muted">No results found</div>';
        return;
    }
    
    container.innerHTML = suggestions.map(suggestion => `
        <div class="search-suggestion-item" onclick="selectSuggestion('${suggestion.value}', '${suggestion.label}')">
            <i class="fas fa-${suggestion.type === 'student' ? 'user' : 'book'} me-2"></i>
            ${suggestion.label}
        </div>
    `).join('');
}

function selectSuggestion(value, label) {
    const activeInput = document.querySelector('.advanced-search:focus');
    if (activeInput) {
        activeInput.value = value;
        hideSuggestions(activeInput.parentNode.querySelector('.search-suggestions'));
    }
}

function hideSuggestions(container) {
    container.style.display = 'none';
}

// Export Features
function initializeExportFeatures() {
    // Enhanced export options with progress tracking
    const exportButtons = document.querySelectorAll('.export-btn');
    exportButtons.forEach(button => {
        button.addEventListener('click', handleExportRequest);
    });
}

function handleExportRequest(e) {
    e.preventDefault();
    const button = e.currentTarget;
    const format = button.dataset.format;
    const endpoint = button.dataset.endpoint;
    
    showExportProgress(button);
    
    // Create a hidden form to handle the export
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = endpoint;
    form.style.display = 'none';
    
    const formatInput = document.createElement('input');
    formatInput.type = 'hidden';
    formatInput.name = 'format';
    formatInput.value = format;
    form.appendChild(formatInput);
    
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
    
    // Reset button after delay
    setTimeout(() => {
        resetExportButton(button);
    }, 3000);
}

function showExportProgress(button) {
    const originalText = button.innerHTML;
    button.dataset.originalText = originalText;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    button.disabled = true;
}

function resetExportButton(button) {
    button.innerHTML = button.dataset.originalText;
    button.disabled = false;
}

// Progress Tracking
function initializeProgressTracking() {
    // Animate progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        animateProgressBar(bar);
    });
}

function animateProgressBar(bar) {
    const targetWidth = bar.style.width;
    bar.style.width = '0%';
    
    setTimeout(() => {
        bar.style.transition = 'width 1s ease-in-out';
        bar.style.width = targetWidth;
    }, 100);
}

// Notifications System
function initializeNotifications() {
    // Set up notification area if it doesn't exist
    if (!document.querySelector('#notification-area')) {
        const notificationArea = document.createElement('div');
        notificationArea.id = 'notification-area';
        notificationArea.className = 'position-fixed top-0 end-0 p-3';
        notificationArea.style.zIndex = '9999';
        document.body.appendChild(notificationArea);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const notificationArea = document.getElementById('notification-area');
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    notificationArea.appendChild(notification);
    
    // Auto-dismiss
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Data Visualization Enhancements
function initializeDataVisualization() {
    // Enhanced chart configurations
    if (typeof Chart !== 'undefined') {
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.position = 'bottom';
        
        // Apply dark theme if needed
        if (document.documentElement.getAttribute('data-bs-theme') === 'dark') {
            Chart.defaults.color = '#fff';
            Chart.defaults.borderColor = '#404040';
            Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        }
    }
    
    // Initialize any charts that need special handling
    initializeCustomCharts();
}

function initializeCustomCharts() {
    // Performance trend charts
    const trendCharts = document.querySelectorAll('.trend-chart');
    trendCharts.forEach(canvas => {
        createTrendChart(canvas);
    });
    
    // Grade distribution charts
    const gradeCharts = document.querySelectorAll('.grade-distribution-chart');
    gradeCharts.forEach(canvas => {
        createGradeChart(canvas);
    });
}

function createTrendChart(canvas) {
    const ctx = canvas.getContext('2d');
    // This would use real data from the backend
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Average Score',
                data: [75, 78, 82, 79, 85, 88],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Performance Trend'
                }
            }
        }
    });
}

function createGradeChart(canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['A+', 'A', 'B+', 'B', 'C+', 'C', 'F'],
            datasets: [{
                data: [15, 25, 20, 18, 12, 8, 2],
                backgroundColor: [
                    '#28a745', '#20c997', '#17a2b8', '#007bff',
                    '#ffc107', '#fd7e14', '#dc3545'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Grade Distribution'
                }
            }
        }
    });
}

// Form Enhancements
function initializeFormEnhancements() {
    // Auto-save functionality
    initializeAutoSave();
    
    // Form validation enhancements
    enhanceFormValidation();
    
    // Dynamic form fields
    initializeDynamicFields();
}

function initializeAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-autosave]');
    autoSaveForms.forEach(form => {
        const formId = form.dataset.autosave;
        const saveKey = `autosave_${formId}`;
        
        // Load saved data
        const savedData = localStorage.getItem(saveKey);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(key => {
                    const field = form.querySelector(`[name="${key}"]`);
                    if (field && field.type !== 'file') {
                        field.value = data[key];
                    }
                });
                showNotification('Previously entered data has been restored', 'info');
            } catch (e) {
                console.error('Error loading autosave data:', e);
            }
        }
        
        // Save on change
        form.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                if (key !== 'csrf_token') {
                    data[key] = value;
                }
            }
            localStorage.setItem(saveKey, JSON.stringify(data));
        }, 1000));
        
        // Clear on submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(saveKey);
        });
    });
}

function enhanceFormValidation() {
    // Custom validation messages
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const invalidFields = form.querySelectorAll(':invalid');
            if (invalidFields.length > 0) {
                e.preventDefault();
                const firstInvalid = invalidFields[0];
                firstInvalid.focus();
                showNotification('Please correct the highlighted fields', 'error');
            }
        });
    });
}

function initializeDynamicFields() {
    // Department-based subject filtering
    const departmentSelects = document.querySelectorAll('select[name="department"]');
    departmentSelects.forEach(select => {
        select.addEventListener('change', updateSubjectOptions);
    });
}

function updateSubjectOptions(e) {
    const department = e.target.value;
    const subjectSelect = document.querySelector('select[name="subject_id"]');
    
    if (subjectSelect) {
        // This would typically fetch subjects for the department via API
        // For now, we'll just show a loading state
        subjectSelect.innerHTML = '<option>Loading subjects...</option>';
        
        setTimeout(() => {
            // Simulate API response
            subjectSelect.innerHTML = `
                <option value="">Select Subject</option>
                <option value="1">${department} - Subject 1</option>
                <option value="2">${department} - Subject 2</option>
            `;
        }, 500);
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Global error handling for bulk operations
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('An unexpected error occurred. Please refresh the page and try again.', 'error');
});

// Export functions for global use
window.SRMS = {
    showNotification,
    handleExportRequest,
    showExportProgress,
    resetExportButton,
    formatFileSize,
    debounce
};
