$(document).ready(function() {
    // Handle alert messages
    setTimeout(() => {
        $(".alert").alert("close");
    }, 3000);

    // Handle copyright year
    const yearElement = document.querySelector('.copyright-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
});