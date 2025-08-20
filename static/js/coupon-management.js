// Coupon Management JavaScript Functions

// Live preview update for add/edit coupon form
function initCouponPreview() {
    const codeInput = document.getElementById('id_code');
    const discountInput = document.getElementById('id_discount');
    const minAmountInput = document.getElementById('id_min_order_amount');
    
    const previewCode = document.getElementById('preview-code');
    const previewDiscount = document.getElementById('preview-discount');
    const previewMin = document.getElementById('preview-min');
    
    function updatePreview() {
        if (codeInput && codeInput.value) {
            previewCode.textContent = codeInput.value.toUpperCase();
            previewCode.classList.add('preview-update');
            setTimeout(() => previewCode.classList.remove('preview-update'), 500);
        }
        if (discountInput && discountInput.value) {
            previewDiscount.textContent = discountInput.value + '% OFF';
            previewDiscount.classList.add('preview-update');
            setTimeout(() => previewDiscount.classList.remove('preview-update'), 500);
        }
        if (minAmountInput && minAmountInput.value) {
            previewMin.textContent = parseFloat(minAmountInput.value).toFixed(2);
            previewMin.classList.add('preview-update');
            setTimeout(() => previewMin.classList.remove('preview-update'), 500);
        }
    }
    
    // Add event listeners
    if (codeInput) codeInput.addEventListener('input', updatePreview);
    if (discountInput) discountInput.addEventListener('input', updatePreview);
    if (minAmountInput) minAmountInput.addEventListener('input', updatePreview);
}

// Enhanced search functionality for coupon list
function initCouponSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    
    // Auto-submit search after typing stops
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.form.submit();
            }, 500); // Wait 500ms after user stops typing
        });
    }
    
    // Add loading state to action buttons
    document.querySelectorAll('.dropdown-item').forEach(link => {
        if (link.href.includes('delete') || link.href.includes('toggle')) {
            link.addEventListener('click', function() {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="material-icons">hourglass_empty</i> Processing...';
                // Restore text if navigation fails
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 3000);
            });
        }
    });
}

// Delete confirmation functionality
function confirmDelete() {
    // Add loading state
    const deleteButton = document.querySelector('#confirmDeleteModal .btn-danger');
    const originalText = deleteButton.innerHTML;
    deleteButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Deleting...';
    deleteButton.disabled = true;
    
    // Submit the form
    setTimeout(() => {
        document.getElementById('deleteCouponForm').submit();
    }, 500); // Small delay for better UX
}

// Keyboard and navigation handlers for delete modal
function initDeleteModalHandlers() {
    // Add escape key handler
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const modal = bootstrap.Modal.getInstance(document.getElementById('confirmDeleteModal'));
            if (modal) {
                modal.hide();
            }
        }
    });

    // Add confirmation when trying to navigate away
    window.addEventListener('beforeunload', function(event) {
        const modal = document.getElementById('confirmDeleteModal');
        if (modal && modal.classList.contains('show')) {
            event.preventDefault();
            event.returnValue = 'Are you sure you want to leave? Your action will not be completed.';
        }
    });
}

// Form validation enhancements
function initCouponFormValidation() {
    const form = document.querySelector('form[method="POST"]');
    if (!form) return;
    
    const codeInput = document.getElementById('id_code');
    const discountInput = document.getElementById('id_discount');
    const minAmountInput = document.getElementById('id_min_order_amount');
    const maxAmountInput = document.getElementById('id_max_discount_amount');
    const expiryDateInput = document.getElementById('id_expiry_date');
    
    // Real-time validation
    if (codeInput) {
        codeInput.addEventListener('blur', function() {
            validateCouponCode(this);
        });
    }
    
    if (discountInput) {
        discountInput.addEventListener('input', function() {
            validateDiscountPercentage(this);
        });
    }
    
    if (minAmountInput && maxAmountInput) {
        [minAmountInput, maxAmountInput].forEach(input => {
            input.addEventListener('input', function() {
                validateAmounts(minAmountInput, maxAmountInput);
            });
        });
    }
    
    if (expiryDateInput) {
        expiryDateInput.addEventListener('change', function() {
            validateExpiryDate(this);
        });
    }
    
    // Form submit validation
    form.addEventListener('submit', function(event) {
        if (!validateForm()) {
            event.preventDefault();
            showValidationErrors();
        }
    });
}

// Individual validation functions
function validateCouponCode(input) {
    const value = input.value.trim().toUpperCase();
    const feedback = input.parentNode.querySelector('.invalid-feedback') || createFeedbackElement(input);
    
    if (value.length < COUPON_CONSTANTS.MIN_COUPON_CODE_LENGTH) {
        const message = VALIDATION_MESSAGES.COUPON_CODE_TOO_SHORT.replace('{min}', COUPON_CONSTANTS.MIN_COUPON_CODE_LENGTH);
        markFieldInvalid(input, message);
        return false;
    }
    
    if (!/^[A-Z0-9]+$/.test(value)) {
        markFieldInvalid(input, VALIDATION_MESSAGES.COUPON_CODE_INVALID_CHARS);
        return false;
    }
    
    markFieldValid(input);
    input.value = value; // Auto-uppercase
    return true;
}

function validateDiscountPercentage(input) {
    const value = parseFloat(input.value);
    
    if (isNaN(value) || value <= COUPON_CONSTANTS.MIN_DISCOUNT_PERCENTAGE || value > COUPON_CONSTANTS.MAX_DISCOUNT_PERCENTAGE) {
        const message = VALIDATION_MESSAGES.DISCOUNT_OUT_OF_RANGE
            .replace('{min}', COUPON_CONSTANTS.MIN_DISCOUNT_PERCENTAGE + 1)
            .replace('{max}', COUPON_CONSTANTS.MAX_DISCOUNT_PERCENTAGE);
        markFieldInvalid(input, message);
        return false;
    }
    
    markFieldValid(input);
    return true;
}

function validateAmounts(minInput, maxInput) {
    const minValue = parseFloat(minInput.value);
    const maxValue = parseFloat(maxInput.value);
    
    let isValid = true;
    
    if (isNaN(minValue) || minValue < COUPON_CONSTANTS.MIN_AMOUNT_VALUE) {
        markFieldInvalid(minInput, VALIDATION_MESSAGES.AMOUNT_NEGATIVE);
        isValid = false;
    } else {
        markFieldValid(minInput);
    }
    
    if (isNaN(maxValue) || maxValue <= COUPON_CONSTANTS.MIN_AMOUNT_VALUE) {
        markFieldInvalid(maxInput, VALIDATION_MESSAGES.AMOUNT_NEGATIVE);
        isValid = false;
    } else if (!isNaN(minValue) && maxValue > minValue) {
        markFieldInvalid(maxInput, VALIDATION_MESSAGES.MAX_DISCOUNT_EXCEEDS_MIN_ORDER);
        isValid = false;
    } else {
        markFieldValid(maxInput);
    }
    
    return isValid;
}

function validateExpiryDate(input) {
    const selectedDate = new Date(input.value);
    const currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0); // Reset time for accurate comparison
    
    if (selectedDate <= currentDate) {
        markFieldInvalid(input, VALIDATION_MESSAGES.EXPIRY_DATE_PAST);
        return false;
    }
    
    markFieldValid(input);
    return true;
}

// Utility functions for validation UI
function markFieldValid(input) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
    const feedback = input.parentNode.querySelector('.invalid-feedback');
    if (feedback) feedback.style.display = 'none';
}

function markFieldInvalid(input, message) {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
    const feedback = input.parentNode.querySelector('.invalid-feedback') || createFeedbackElement(input);
    feedback.textContent = message;
    feedback.style.display = 'block';
}

function createFeedbackElement(input) {
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    input.parentNode.appendChild(feedback);
    return feedback;
}

function validateForm() {
    const codeInput = document.getElementById('id_code');
    const discountInput = document.getElementById('id_discount');
    const minAmountInput = document.getElementById('id_min_order_amount');
    const maxAmountInput = document.getElementById('id_max_discount_amount');
    const expiryDateInput = document.getElementById('id_expiry_date');
    
    let isValid = true;
    
    if (codeInput && !validateCouponCode(codeInput)) isValid = false;
    if (discountInput && !validateDiscountPercentage(discountInput)) isValid = false;
    if (minAmountInput && maxAmountInput && !validateAmounts(minAmountInput, maxAmountInput)) isValid = false;
    if (expiryDateInput && !validateExpiryDate(expiryDateInput)) isValid = false;
    
    return isValid;
}

function showValidationErrors() {
    const firstInvalidField = document.querySelector('.is-invalid');
    if (firstInvalidField) {
        firstInvalidField.focus();
        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Initialize all coupon management functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("Coupon Management JS Loaded");

    // Logic cho trang Add/Edit Coupon
    if (document.getElementById('preview-code')) {
        console.log("Initializing Coupon Preview...");
        initCouponPreview();
    }

    // Logic cho trang danh sách Coupons
    if (document.querySelector('input[name="search"]')) {
        console.log("Initializing Coupon Search...");
        initCouponSearch();
    }

    // Logic cho trang Delete Coupon
    if (document.getElementById('confirmDeleteModal')) {
        console.log("Initializing Delete Modal Handlers...");
        // Các event listener cho modal đã được Bootstrap xử lý
        // Chỉ cần đảm bảo hàm confirmDelete được gọi đúng lúc
    }
});

// Export functions for global access
window.confirmDelete = confirmDelete;