$(document).ready(function() {
    // Handle copyright year
    const yearElement = document.querySelector('.copyright-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // Global form enhancements
    initGlobalFormFeatures();
    
    // Global loading states
    initGlobalLoadingStates();
});

// Global form enhancement functions
function initGlobalFormFeatures() {
    // Auto-focus first invalid field on form submission
    document.addEventListener('invalid', function(event) {
        event.target.focus();
        event.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, true);
    
    // Add floating labels support
    document.querySelectorAll('.form-floating input, .form-floating textarea').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.classList.add('has-value');
            } else {
                this.classList.remove('has-value');
            }
        });
    });
    
    // Enhanced select styling
    document.querySelectorAll('select.form-select').forEach(select => {
        select.addEventListener('change', function() {
            this.classList.add('selected');
        });
    });
}

// Global loading states for forms and buttons
function initGlobalLoadingStates() {
    // Add loading state to form submissions
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                
                // Restore button if form validation fails
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }, 5000);
            }
        });
    });
    
    // Add loading state to delete links
    document.querySelectorAll('a[href*="delete"]').forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
                return false;
            }
            
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="material-icons">hourglass_empty</i> Deleting...';
            this.style.pointerEvents = 'none';
            
            // Restore if navigation fails
            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.pointerEvents = '';
            }, 3000);
        });
    });
}

// Export utility functions for global access
// Removed showToast function - no longer using toast notifications