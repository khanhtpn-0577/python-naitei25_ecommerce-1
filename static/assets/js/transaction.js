$(document).ready(function () {
    // Select all checkbox functionality
    $('#transactionCheck01').change(function () {
        $('tbody input[type="checkbox"]').prop('checked', this.checked);
    });

    // Hover effects for table rows
    $('.table tbody tr').hover(
        function () {
            $(this).addClass('table-hover-effect');
        },
        function () {
            $(this).removeClass('table-hover-effect');
        }
    );

    // Smooth scroll to top on page load
    $('html, body').animate({ scrollTop: 0 }, 'slow');

    // Add click effects to cards
    $('.card').on('click', function (e) {
        if (!$(e.target).is('input, button, a, select')) {
            $(this).addClass('card-click-effect');
            setTimeout(() => {
                $(this).removeClass('card-click-effect');
            }, 200);
        }
    });
});
