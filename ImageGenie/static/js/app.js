/**
 * Student Result Management System
 * Frontend JavaScript Functions
 */

// Global SRMS object for shared functionality
const SRMS = {
    showNotification: function(message, type = 'info', duration = 5000) {
        // Create notification area if it doesn't exist
        let notificationArea = document.getElementById('notification-area');
        if (!notificationArea) {
            notificationArea = document.createElement('div');
            notificationArea.id = 'notification-area';
            notificationArea.className = 'position-fixed top-0 end-0 p-3';
            notificationArea.style.zIndex = '9999';
            document.body.appendChild(notificationArea);
        }
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        notificationArea.appendChild(notification);
        
        // Auto-dismiss notification
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    initializeTooltips();
    initializePopovers();
    initializeFormValidation();
    initializeFileUploads();
    initializeSearchFeatures();
    initializeAnimations();
    
    console.log('Student Result Management System initialized successfully');
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Form validation enhancements
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation for specific fields
    initializeRealTimeValidation();
}

// Real-time validation for form fields
function initializeRealTimeValidation() {
    // Roll number validation
    const rollNoInputs = document.querySelectorAll('input[name="roll_no"]');
    rollNoInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.toUpperCase();
            this.value = value;
            
            // Basic pattern validation
            const isValid = /^[A-Z0-9]{6,}$/.test(value);
            this.setCustomValidity(isValid ? '' : 'Roll number must be at least 6 characters (letters and numbers only)');
        });
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value && !isValidEmail(this.value)) {
                this.setCustomValidity('Please enter a valid email address');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Phone validation
    const phoneInputs = document.querySelectorAll('input[name="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.replace(/\D/g, '');
            if (value.length > 0 && value.length < 10) {
                this.setCustomValidity('Phone number must be at least 10 digits');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    // Marks validation
    const marksInputs = document.querySelectorAll('input[name="marks_obtained"]');
    marksInputs.forEach(input => {
        input.addEventListener('input', function() {
            const totalMarksInput = document.querySelector('input[name="total_marks"]');
            const obtainedMarks = parseFloat(this.value);
            const totalMarks = parseFloat(totalMarksInput?.value || 100);
            
            if (obtainedMarks > totalMarks) {
                this.setCustomValidity('Marks obtained cannot be greater than total marks');
            } else if (obtainedMarks < 0) {
                this.setCustomValidity('Marks cannot be negative');
            } else {
                this.setCustomValidity('');
            }
            
            // Update grade preview
            updateGradePreview(obtainedMarks, totalMarks);
        });
    });
}

// File upload enhancements
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                validateFile(file, this);
                previewFile(file, this);
            }
        });
        
        // Drag and drop functionality
        const container = input.closest('.file-upload-container');
        if (container) {
            setupDragAndDrop(container, input);
        }
    });
}

// File validation
function validateFile(file, input) {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    let isValid = true;
    let message = '';
    
    if (!allowedTypes.includes(file.type)) {
        isValid = false;
        message = 'Please select a JPG, JPEG, or PNG image';
    } else if (file.size > maxSize) {
        isValid = false;
        message = 'File size must be less than 5MB';
    }
    
    if (!isValid) {
        input.setCustomValidity(message);
        showAlert(message, 'danger');
        input.value = '';
    } else {
        input.setCustomValidity('');
    }
    
    return isValid;
}

// File preview functionality
function previewFile(file, input) {
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewContainer = input.parentNode.querySelector('.file-preview');
            if (previewContainer) {
                previewContainer.innerHTML = `
                    <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
                    <p class="text-muted mt-2">${file.name} (${formatFileSize(file.size)})</p>
                `;
            }
        };
        reader.readAsDataURL(file);
    }
}

// Drag and drop setup
function setupDragAndDrop(container, input) {
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
        container.classList.add('dragover');
    });
    
    container.addEventListener('dragleave', function(e) {
        e.preventDefault();
        container.classList.remove('dragover');
    });
    
    container.addEventListener('drop', function(e) {
        e.preventDefault();
        container.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// Search functionality enhancements
function initializeSearchFeatures() {
    const searchInputs = document.querySelectorAll('.search-input, input[name="search"]');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value, this);
            }, 500);
        });
    });
}

// Perform search with debouncing
function performSearch(query, input) {
    if (query.length < 2) return;
    
    // Add search suggestions or live results here
    console.log('Searching for:', query);
}

// Animation initialization
function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
    
    // Animate statistics on scroll
    initializeCounterAnimations();
    initializeScrollAnimations();
}

// Counter animations for statistics
function initializeCounterAnimations() {
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += step;
                counter.textContent = Math.floor(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        // Start animation when element is in viewport
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// Scroll animations
function initializeScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => observer.observe(el));
}

// Grade calculation and preview
function updateGradePreview(obtained, total) {
    const percentage = (obtained / total) * 100;
    let grade = calculateGrade(percentage);
    
    // Update grade preview if element exists
    const gradePreview = document.querySelector('.grade-preview');
    if (gradePreview) {
        gradePreview.innerHTML = `
            <span class="badge bg-${getGradeColor(grade)}">
                ${percentage.toFixed(1)}% - Grade ${grade}
            </span>
        `;
    }
}

// Calculate grade from percentage
function calculateGrade(percentage) {
    if (percentage >= 90) return 'A+';
    if (percentage >= 80) return 'A';
    if (percentage >= 70) return 'B+';
    if (percentage >= 60) return 'B';
    if (percentage >= 50) return 'C+';
    if (percentage >= 40) return 'C';
    return 'F';
}

// Get color class for grade
function getGradeColor(grade) {
    const colors = {
        'A+': 'success', 'A': 'success',
        'B+': 'primary', 'B': 'primary',
        'C+': 'warning', 'C': 'warning',
        'F': 'danger'
    };
    return colors[grade] || 'secondary';
}

// Utility functions
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function confirmDelete(itemName, callback) {
    const message = `Are you sure you want to delete "${itemName}"? This action cannot be undone.`;
    confirmAction(message, callback);
}

// Export functions
function exportData(format, endpoint) {
    showAlert('Preparing export...', 'info', 2000);
    window.location.href = endpoint + '?format=' + format;
}

// Print functionality
function printPage() {
    window.print();
}

function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                    <style>
                        body { padding: 20px; }
                        .btn, .no-print { display: none !important; }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
}

// Data visualization helpers
function initializeCharts() {
    // Chart.js default configuration
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.plugins.legend.position = 'bottom';
    
    // Common chart colors
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#C9CBCF', '#4BC0C0'
    ];
    
    return colors;
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.warn('Could not save to localStorage:', error);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.warn('Could not load from localStorage:', error);
        return defaultValue;
    }
}

// Theme management
function initializeTheme() {
    const savedTheme = loadFromLocalStorage('theme', 'dark');
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    saveToLocalStorage('theme', newTheme);
}

// Auto-save form data
function initializeAutoSave() {
    const forms = document.querySelectorAll('form[data-autosave]');
    
    forms.forEach(form => {
        const formId = form.getAttribute('data-autosave');
        
        // Load saved data
        const savedData = loadFromLocalStorage(`form_${formId}`);
        if (savedData) {
            Object.keys(savedData).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input && input.type !== 'file') {
                    input.value = savedData[key];
                }
            });
        }
        
        // Save on input
        form.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                if (key !== 'csrf_token') {
                    data[key] = value;
                }
            }
            saveToLocalStorage(`form_${formId}`, data);
        }, 1000));
        
        // Clear on submit
        form.addEventListener('submit', () => {
            localStorage.removeItem(`form_${formId}`);
        });
    });
}

// Debounce utility function
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

// Initialize theme on load
initializeTheme();

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showAlert('An error occurred. Please try again or contact support.', 'danger');
});

// Service worker registration (if needed)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered:', registration))
            .catch(error => console.log('SW registration failed:', error));
    });
}
