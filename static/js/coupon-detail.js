class CouponDetailManager {
    constructor(couponId, couponsListUrl) {
        this.deleteConfirmModal = null;
        this.confirmDeleteBtn = null;
        this.deleteUrl = '';
        this.couponId = couponId;
        this.couponsListUrl = couponsListUrl;
        this.csrfToken = '';
        
        this.init();
    }
    
    init() {
        this.deleteConfirmModal = document.getElementById('deleteConfirmModal');
        this.confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        
        this.csrfToken = this.getCSRFToken();
        
        this.bindEvents();
    }
    
    getCSRFToken() {
        if (window.csrfToken) {
            return window.csrfToken;
        }
        
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    bindEvents() {
        if (!this.deleteConfirmModal) return;
        
        // Modal show event
        this.deleteConfirmModal.addEventListener('show.bs.modal', (event) => {
            this.handleModalShow(event);
        });
        
        // Confirm delete button click
        this.confirmDeleteBtn.addEventListener('click', () => {
            this.handleDeleteConfirm();
        });
        
        // Handle modal keyboard events
        this.deleteConfirmModal.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !this.confirmDeleteBtn.disabled) {
                event.preventDefault();
                this.confirmDeleteBtn.click();
            }
        });
    }
    
    handleModalShow(event) {
        const button = event.relatedTarget;
        this.deleteUrl = button.getAttribute('data-delete-url');
        
        // Reset button state
        this.toggleButtonLoading(false);
    }
    
    toggleButtonLoading(isLoading) {
        const btnText = this.confirmDeleteBtn.querySelector('.btn-text');
        const btnLoading = this.confirmDeleteBtn.querySelector('.btn-loading');
        
        if (isLoading) {
            btnText.classList.add('d-none');
            btnLoading.classList.remove('d-none');
            this.confirmDeleteBtn.disabled = true;
        } else {
            btnText.classList.remove('d-none');
            btnLoading.classList.add('d-none');
            this.confirmDeleteBtn.disabled = false;
        }
    }
    
    handleDeleteConfirm() {
        if (!this.deleteUrl) return;

        this.toggleButtonLoading(true);

        fetch(this.deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            this.toggleButtonLoading(false);
            
            const modal = bootstrap.Modal.getInstance(this.deleteConfirmModal);
            modal.hide();
            
            if (data.success) {
                // Redirect to coupons list immediately
                window.location.href = this.couponsListUrl;
            } else {
                alert(data.error || 'An error occurred while deleting the coupon.');
            }
        })
        .catch(error => {
            this.toggleButtonLoading(false);
            console.error('Error:', error);
            
            const modal = bootstrap.Modal.getInstance(this.deleteConfirmModal);
            modal.hide();
            
            alert('An unexpected error occurred.');
        });
    }
}

// Global function to initialize coupon detail manager
window.initCouponDetailManager = function(couponId, couponsListUrl) {
    new CouponDetailManager(couponId, couponsListUrl);
};
