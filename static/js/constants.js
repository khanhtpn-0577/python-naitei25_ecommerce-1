const COUPON_CONSTANTS = {
    MIN_COUPON_CODE_LENGTH: 3,
    MIN_DISCOUNT_PERCENTAGE: 0,
    MAX_DISCOUNT_PERCENTAGE: 100,
    MIN_AMOUNT_VALUE: 0
};

const PRODUCT_CONSTANTS = {
    MIN_PRODUCT_PRICE: 0.01,
    MIN_AMOUNT_VALUE: 0
};

const VALIDATION_MESSAGES = {
    COUPON_CODE_TOO_SHORT: 'Coupon code must be at least {min} characters long',
    COUPON_CODE_INVALID_CHARS: 'Coupon code can only contain letters and numbers',
    DISCOUNT_OUT_OF_RANGE: 'Discount must be between {min} and {max} percent',
    AMOUNT_NEGATIVE: 'Amount cannot be negative',
    MAX_DISCOUNT_EXCEEDS_MIN_ORDER: 'Maximum discount should not exceed minimum order amount',
    EXPIRY_DATE_PAST: 'Expiry date must be in the future'
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        COUPON_CONSTANTS,
        PRODUCT_CONSTANTS,
        VALIDATION_MESSAGES
    };
} else {
    window.COUPON_CONSTANTS = COUPON_CONSTANTS;
    window.PRODUCT_CONSTANTS = PRODUCT_CONSTANTS;
    window.VALIDATION_MESSAGES = VALIDATION_MESSAGES;
}
