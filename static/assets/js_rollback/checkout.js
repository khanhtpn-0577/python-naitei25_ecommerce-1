$(document).ready(function () {
    // Mock PayPal Integration
    paypal.Buttons({
        createOrder: function (data, actions) {
            return actions.order.create({
                purchase_units: [{
                    amount: {
                        value: "320.21",
                    },
                }],
            });
        },
        onApprove: function (data, actions) {
            return actions.order.capture().then(function (details) {
                console.log(details);
                if (details.status === "COMPLETED") {
                    $('#successModal').modal('show');
                }
            });
        },
        onError: function (err) {
            console.error('PayPal Error:', err);
            alert(PAYMENT_FAIL_MSG);  // lấy từ biến global
        }
    }).render("#paypal-button-container");

    // Mock Stripe Integration
    $('#checkout-button').on('click', function () {
        var button = $(this);
        var originalText = button.html();

        button.html('<i class="fas fa-spinner fa-spin me-2"></i>' + PROCESSING_MSG);
        button.prop('disabled', true);

        setTimeout(function () {
            button.html(originalText);
            button.prop('disabled', false);
            $('#successModal').modal('show');
        }, 2000);
    });

    // Cash on Delivery
    $('#cod-button').on('click', function () {
        if (confirm(CONFIRM_COD_MSG)) {
            $('#successModal').modal('show');
        }
    });

    // Coupon form handling
    $('.apply-coupon').on('submit', function (e) {
        e.preventDefault();
        var code = $('input[name="code"]').val();

        if (code) {
            if (code.toLowerCase() === 'save10') {
                alert(COUPON_SUCCESS_MSG);
                $('.cart-totals p:contains("Discount")').next().text('-$20.00');
                $('.cart-totals .text-primary').text('$310.21');
            } else {
                alert(COUPON_INVALID_MSG);
            }
        } else {
            alert(COUPON_EMPTY_MSG);
        }
    });
});
