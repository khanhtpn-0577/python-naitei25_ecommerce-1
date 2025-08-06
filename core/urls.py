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
    path("checkout/", checkout, name="checkout"),
    # path("payment-completed/", payment_completed_view, name="payment-completed"),
    # path("payment-failed/", payment_failed_view, name="payment-failed"),
    # path("dashboard/order/<id>/", order_detail, name="order-detail"),
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
    path("vendors/", vendor_list_view, name="vendor-list"),
#     path("product/<pid>/", product_detail_view, name="product-detail"),
#     path("vendors/", vendor_list_view, name="vendor-list"),
#     path("vendor/<vid>/", vendor_detail_view, name="vendor-detail"),
]