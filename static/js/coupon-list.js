class CouponListManager {
    constructor() {
        this.deleteConfirmModal = null;
        this.confirmDeleteBtn = null;
        this.couponCodeDisplay = null;
        this.couponDetails = null;
        this.deleteUrl = '';
        this.couponIdToDelete = null;
        this.couponCode = '';
        this.csrfToken = '';
        
        this.init();
    }
    
    init() {
        this.deleteConfirmModal = document.getElementById('deleteConfirmModal');
        this.confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        this.couponCodeDisplay = document.getElementById('coupon-code-display');
        this.couponDetails = document.getElementById('coupon-details');
        
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
        
        this.deleteConfirmModal.addEventListener('show.bs.modal', (event) => {
            this.handleModalShow(event);
        });
        
        this.confirmDeleteBtn.addEventListener('click', () => {
            this.handleDeleteConfirm();
        });
        
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
        this.couponIdToDelete = button.getAttribute('data-coupon-id');
        
        const row = button.closest('tr');
        this.couponCode = row ? 
            row.querySelector('td:first-child .coupon-code')?.textContent.trim() || 'Unknown' : 
            'Unknown';
        
        if (this.couponCodeDisplay) {
            this.couponCodeDisplay.textContent = this.couponCode;
        }
        
        if (this.deleteUrl) {
            this.loadCouponDetails(this.deleteUrl);
        }
        
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
    
    loadCouponDetails(url) {
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.coupon && this.couponDetails) {
                const coupon = data.coupon;
                this.couponDetails.innerHTML = `
                    <table class="table table-borderless table-sm mb-0">
                        <tr>
                            <td><strong>Discount:</strong></td>
                            <td>${coupon.discount}%</td>
                        </tr>
                        <tr>
                            <td><strong>Expiry Date:</strong></td>
                            <td>${coupon.expiry_date}</td>
                        </tr>
                        <tr>
                            <td><strong>Status:</strong></td>
                            <td>
                                <span class="badge ${coupon.active ? 'bg-success' : 'bg-secondary'}">
                                    ${coupon.active ? 'Active' : 'Inactive'}
                                </span>
                            </td>
                        </tr>
                    </table>
                `;
                this.couponDetails.classList.remove('d-none');
            }
        })
        .catch(error => {
            console.error('Error loading coupon details:', error);
            if (this.couponDetails) {
                this.couponDetails.classList.add('d-none');
            }
        });
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
                if (data.deleted) {
                    this.removeCouponRow();
                    this.showSuccessMessage(data.message);
                }
            } else {
                // Show error message
                if (data.used_in_orders) {
                    this.showErrorMessage(data.error + ' Please use the "Deactivate" option instead.');
                } else {
                    this.showErrorMessage(data.error || 'An error occurred while deleting the coupon.');
                }
            }
        })
        .catch(error => {
            this.toggleButtonLoading(false);
            console.error('Error:', error);
            
            const modal = bootstrap.Modal.getInstance(this.deleteConfirmModal);
            modal.hide();
            
            this.showErrorMessage('An unexpected error occurred.');
        });
    }

    showErrorMessage(message) {
        // Create a temporary error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="material-icons md-error me-2" style="font-size: 16px; vertical-align: text-bottom;"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the content main area and prepend the alert
        const contentMain = document.querySelector('.content-main');
        if (contentMain) {
            contentMain.insertBefore(alertDiv, contentMain.firstChild);
            
            // Auto dismiss after 8 seconds (longer for error messages)
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 8000);
        }
    }
    
    removeCouponRow() {
        const couponRow = document.querySelector(`tr[data-coupon-id='${this.couponIdToDelete}']`);
        if (couponRow) {
            // Add fade out animation
            couponRow.style.transition = 'opacity 0.3s ease';
            couponRow.style.opacity = '0';
            
            setTimeout(() => {
                couponRow.remove();
                
                // Check if table is empty
                const tbody = couponRow.closest('tbody');
                if (tbody && tbody.children.length === 0) {
                    // Reload the page if no coupons left
                    location.reload();
                }
            }, 300);
        }
    }
    
    showSuccessMessage(message) {
        // Create a temporary success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.innerHTML = `
            <i class="material-icons md-check_circle me-2" style="font-size: 16px; vertical-align: text-bottom;"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Find the content main area and prepend the alert
        const contentMain = document.querySelector('.content-main');
        if (contentMain) {
            contentMain.insertBefore(alertDiv, contentMain.firstChild);
            
            // Auto dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the coupon list page
    if (document.getElementById('deleteConfirmModal')) {
        new CouponListManager();
    }
});
