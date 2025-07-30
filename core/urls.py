from django import views
from django.urls import path, include
from core.views import product_list_view, about_us, customer_dashboard, search_view, index, checkout, payment_completed_view, payment_failed_view

app_name = "core"

urlpatterns = [
    path("", index, name="index"),
    path("products/", product_list_view, name="product-list"),
    path("about_us/", about_us, name="about_us"),
    path("dashboard/", customer_dashboard, name="dashboard"),
    path("search/", search_view, name="search"),
    path("checkout/", checkout, name="checkout"),
    path("payment-completed/", payment_completed_view, name="payment-completed"),
    path("payment-failed/", payment_failed_view, name="payment-failed"),

]