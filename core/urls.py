from django import views
from django.urls import path, include
from core.views import *

app_name = "core"

urlpatterns = [
    path("", index, name="index"),
    path("products/", product_list_view, name="product-list"),
    path("products/<pid>/", product_detail_view, name="product-detail"),


    path("about_us/", about_us, name="about_us"),
    path("dashboard/", customer_dashboard, name="dashboard"),
    path("payment-completed/", payment_completed_view, name="payment-completed"),
    path("payment-failed/", payment_failed_view, name="payment-failed"),
    path("dashboard/order/<id>/", order_detail, name="order-detail"),
    path("category/", category_list_view, name="category-list"),
    path("category/<cid>/", category_product_list_view, name="category-product-list"),

     # Homepage
    path("cart/", cart_view, name="cart"),
    path("add-to-cart/", add_to_cart, name="add-to-cart"),
    path("delete-from-cart/", delete_item_from_cart, name="delete-from-cart"),
    path("update-cart/", update_cart, name="update-cart"),
    path("ajax-add-review/<int:pid>/", ajax_add_review, name="ajax-add-review"),
    path("products/", product_list_view, name="product-list"),
    path("search/", search_view, name="search"),
    path("product/<pid>/", product_detail_view, name="product-detail"),
    path("vendors/", vendor_list_view, name="vendor-list"),
    path("vendor/<vid>/", vendor_detail_view, name="vendor-detail"),
    path("search/", search_view, name="search"),

    #add review
    path("ajax-add-review/<pid>", ajax_add_review, name="ajax-add-review"),
    path("paypal/", include("paypal.standard.ipn.urls")),
    path("checkout/cod/", cod_checkout, name="cod-checkout"),
    path("checkout/cod/<int:oid>/", cod_detail, name="cod-detail"),
    path("checkout/cod/<int:oid>/accept/", cod_accept, name="cod-accept"),
    path("checkout/<int:oid>/", checkout, name="checkout"),
    path("orders/", order_list, name="orders"),  
    path("filter-products/", filter_product, name="filter-product"),
      # Dashboard URL
    path("dashboard/", customer_dashboard, name="dashboard"),
    path("make-default-address/", make_address_default, name="make-default-address"),
]
