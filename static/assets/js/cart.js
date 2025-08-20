document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input[type=number].product-qty").forEach(function (input) {
    input.addEventListener("change", function () {
      let productId = this.dataset.product;
      let newQty = this.value;

      fetch(updateCartUrl + "?id=" + productId + "&qty=" + newQty)
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // cập nhật lại input nếu bị chỉnh vượt quá stock hoặc <1
            this.value = data.qty;

            // update subtotal
            let subtotalCell = this.closest("tr").querySelector(".price h4.text-brand");
            subtotalCell.textContent = "$" + parseFloat(data.subtotal).toFixed(2);

            // update summary
            let summarySubtotal = document.querySelector("#summary-subtotal");
            if (summarySubtotal) {
              summarySubtotal.textContent = "$" + parseFloat(data.cart_total).toFixed(2);
            }

            let summaryTotal = document.querySelector("#summary-total");
            if (summaryTotal) {
              summaryTotal.textContent = "$" + parseFloat(data.cart_total).toFixed(2);
            }

            // hiện thông báo nếu có
            if (data.message) {
              alert(data.message);
            }
          }
        })
        .catch(err => console.error("Update cart failed:", err));
    });
  });
});
