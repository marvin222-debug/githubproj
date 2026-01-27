// Common functions for the ANPR system website

// Add active class to current navigation item
document.addEventListener('DOMContentLoaded', function() {
    // Get current page path
    const path = window.location.pathname;
    
    // Find nav links
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    // Set active class
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === path) {
            link.classList.add('active');
        }
    });
    
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    return date.toLocaleDateString();
}

// Format vehicle age
function formatAge(years) {
    if (years === undefined || years === null) return 'N/A';
    
    if (years < 1) {
        const months = Math.round(years * 12);
        return `${months} month${months !== 1 ? 's' : ''}`;
    }
    
    return `${Math.round(years * 10) / 10} years`;
}

// Add visual feedback to form buttons
function addFormButtonFeedback() {
    const buttons = document.querySelectorAll('form:not(#check-form) button[type="submit"]');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form.checkValidity()) {
                // Add loading state
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...';
                this.disabled = true;
                
                // Enable after a timeout in case of network issues
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = this.getAttribute('data-original-text') || 'Submit';
                }, 10000);
                
                // Store original text
                if (!this.getAttribute('data-original-text')) {
                    this.setAttribute('data-original-text', this.innerHTML);
                }
            }
        });
    });
}

// Handle errors
function handleApiError(error, errorContainer, errorMessage) {
    console.error('API Error:', error);
    errorMessage.textContent = 'Network error or server issue. Please try again.';
    errorContainer.classList.remove('d-none');
}

// Initialize form button feedback on all pages
document.addEventListener('DOMContentLoaded', addFormButtonFeedback); 
