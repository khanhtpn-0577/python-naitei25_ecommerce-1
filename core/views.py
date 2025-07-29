from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index (request):
    return render(request, 'core/index.html')

def product_list_view(request):
    return render(request, 'core/product-list.html')

def about_us(request):
    return render(request, "core/about_us.html")

def customer_dashboard(request):
    return render(request, 'core/dashboard.html')

def search_view(request):
    return render(request, "core/search.html")

def checkout(request):
    context = {}
    return render(request, "core/checkout.html", context)

def payment_completed_view(request):
    # Mock data cho template testing
    sample_order = {
        'oid': 'ORD-12345',
        'total': 320.21,
        'paid_status': True,
        'created_date': '2024-01-15',
        'payment_method': 'Credit Card'
    }
    
    context = {
        "order": sample_order,
    }
    return render(request, 'core/payment-completed.html', context)

def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')