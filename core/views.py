from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import Product
from django.template.loader import render_to_string
from django.db.models import Avg
from core.models import ProductReview
from django.shortcuts import get_object_or_404
from core.models import *
from core.models import Image
from core.models import Vendor
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Category
import core.constants as C
from core.constants import TAG_LIMIT
from core.models import Coupon, Product, Category, Vendor, CartOrder, CartOrderProducts, Image, ProductReview, Address
# Create your views here.
from taggit.models import Tag
from core.constants import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Product, Image

def index(request):
    # Base query: các sản phẩm đã publish
    base_query = Product.objects.filter(product_status=C.STATUS_PUBLISHED).order_by("-pid")

    # Featured products
    products = base_query.filter(featured=True)

    # Các category cần lọc
    categories = {
        "products_milk": "Milks & Dairies",
        "products_tea": "Coffees & Teas",
        "products_pet": "Pet Foods",
        "products_meat": "Meats",
        "products_veg": "Vegetables",
        "products_fruit": "Fruits",
    }

    # Lọc theo từng category một cách tự động
    category_products = {
        key: base_query.filter(category__title=value)
        for key, value in categories.items()
    }

    # Lấy ảnh đại diện của từng product (chỉ cho featured)
    product_images = {}
    for p in products:
        img = Image.objects.filter(
            object_type='Product',
            object_id=p.pid,
            is_primary=True
        ).first()
        product_images[p.pid] = img.image.url if img else None

    # Gộp context lại
    context = {
        'products': products,
        'product_images': product_images,
        **category_products  # unpack luôn dict vào context
    }

    return render(request, 'core/index.html', context)

@login_required
def cart_view(request):
    cart_total_amount = 0
    cart_items = {}

    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            try:
                price = float(item.get('price', 0) or 0)
                qty = int(item.get('qty', 1))
                subtotal = qty * price
            except (ValueError, TypeError):
                price = 0
                qty = 0
                subtotal = 0

            item['subtotal'] = subtotal
            cart_items[p_id] = item
            cart_total_amount += subtotal

        return render(request, "core/cart.html", {
            "cart_data": cart_items,
            'totalcartitems': len(cart_items),
            'cart_total_amount': cart_total_amount
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")

def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['id'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:

            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data

    else:
        request.session['cart_data_obj'] = cart_product
    return JsonResponse({"data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj'])})

@login_required
def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-table.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

@login_required
def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-table.html", {"cart_data":request.session['cart_data_obj'], 'totalcartitems': len(request.session['cart_data_obj']), 'cart_total_amount':cart_total_amount})
    return JsonResponse({"data": context, 'totalcartitems': len(request.session['cart_data_obj'])})

@login_required
def ajax_add_review(request, pid):
    product = Product.objects.get(pk=pid)
    user = request.user

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review = request.POST['review'],
        rating = request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg("rating"))

    return JsonResponse(
       {
         'bool': True,
        'context': context,
        'average_reviews': average_reviews
       }
    )
def product_list_view(request):
    products = Product.objects.filter(product_status="published").order_by("-pid")
    tags = Tag.objects.all().order_by("-id")[:TAG_LIMIT]

    context = {
        "products":products,
        "tags":tags,
    }

    return render(request, 'core/product-list.html', context)

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
    context = {
        "order": get_sample_order(),
    }
    return render(request, 'core/payment-completed.html', context)

def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

def order_detail(request, id):
    context = {"order_items": get_order_items()}
    return render(request, 'core/order-detail.html', context)

def category_list_view(request):
    categories = Category.objects.all()
    category_data = []

    for cat in categories:
        image = Image.objects.filter(
            object_type='Category',
            object_id=cat.cid,
            is_primary=True
        ).first()

        category_data.append({
            "cid": cat.cid,
            "title": cat.title,
            "alt_text": image.alt_text if image else "",
            "image_url": image.image.url if image else DEFAULT_CATEGORY_IMAGE
        })

    return render(request, "core/category-list.html", {
        "categories": category_data
    })


def category_product_list_view(request, cid):
    category = get_object_or_404(Category, cid=cid)

    products = Product.objects.filter(category=category, product_status=PRODUCT_STATUS_PUBLISHED)

    # Gán thêm thuộc tính image_url và alt_text (không ghi đè thuộc tính @property image)
    for product in products:
        primary_image = Image.objects.filter(
            object_type='Product',
            object_id=product.pid,
            is_primary=True
        ).first()
        product.image_url = primary_image.image.url if primary_image else DEFAULT_PRODUCT_IMAGE
        product.alt_text = primary_image.alt_text if primary_image else product.title

    context = {
        "category": category,
        "products": products,

    }
    return render(request, "core/category-product-list.html", context)


def product_detail_view(request, pid):
    #product = Product.objects.get(pid = pid)
    # Lấy product theo pid, nếu không tìm thấy -> raise 404
    product = get_object_or_404(Product, pid=pid)
    products = Product.objects.filter(category=product.category).exclude(pid=pid)[:4]
    address = None
    if request.user.is_authenticated:
        address = Address.objects.filter(user=request.user).first()

    context = {
        "p": product,
        "address": address,
        "products": products
    }

    return render(request, "core/product-detail.html", context)

def vendor_list_view(request):
    # Get search parameter
    search_query = request.GET.get('search', '')

    # Get sort parameter from request with validation
    sort_by = request.GET.get('sort', 'title')
    order = request.GET.get('order', 'asc')

    # Validate sort_by parameter
    valid_sort_fields = ['title', 'date', 'authentic_rating', 'shipping_on_time', 'chat_resp_time']
    if sort_by not in valid_sort_fields:
        sort_by = 'title'

    # Validate order parameter
    if order not in ['asc', 'desc']:
        order = 'asc'

    # Get page parameter
    page_number = request.GET.get('page', 1)

    vendors = Vendor.objects.all()

    # Apply search filter
    if search_query:
        vendors = vendors.filter(
            Q(title__icontains=search_query) |
            Q(vid__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # Apply sorting with improved logic
    sort_mapping = {
        'title': 'title',
        'date': 'date',
        'authentic_rating': 'authentic_rating',
        'shipping_on_time': 'shipping_on_time',
        'chat_resp_time': 'chat_resp_time'
    }

    sort_field = sort_mapping.get(sort_by, 'title')
    if order == 'desc':
        sort_field = f'-{sort_field}'

    vendors = vendors.order_by(sort_field)

    # Apply pagination
    paginator = Paginator(vendors, 12)  # Show 12 vendors per page
    page_obj = paginator.get_page(page_number)



    context = {
        "vendors": page_obj,
        "sort_by": sort_by,
        "order": order,
        "search_query": search_query,
        "page_obj": page_obj,
        "get_sorting_url": get_sorting_url,
        "base_params": {"search": search_query} if search_query else {},
    }
    return render(request, "core/vendor-list.html", context)

def vendor_detail_view(request, vid):
    vendor = Vendor.objects.get(vid=vid)

    # Get sort parameters for products with validation
    sort_by = request.GET.get('sort', 'date')
    order = request.GET.get('order', 'desc')

    # Validate sort_by parameter
    valid_sort_fields = ['date', 'title', 'price', 'rating']
    if sort_by not in valid_sort_fields:
        sort_by = 'date'

    # Validate order parameter
    if order not in ['asc', 'desc']:
        order = 'desc'

    products = Product.objects.filter(vendor=vendor, product_status="published")

    # Apply sorting to products with improved logic
    sort_mapping = {
        'date': 'date',
        'title': 'title',
        'price': 'amount',
        'rating': 'rating_avg'
    }

    sort_field = sort_mapping.get(sort_by, 'date')
    if order == 'desc':
        sort_field = f'-{sort_field}'

    products = products.order_by(sort_field)

    categories = Category.objects.all()

    context = {
        "vendor": vendor,
        "products": products,
        "categories": categories,
        "sort_by": sort_by,
        "order": order,
        "get_sorting_url": get_sorting_url,
        "base_params": {},
    }
    return render(request, "core/vendor-detail.html", context)

def get_sorting_url(request, sort_by, order):
    params = request.GET.copy()
    params['sort'] = sort_by
    params['order'] = order
    return f"{request.path}?{params.urlencode()}"

def search_view(request):
    query = request.GET.get("q", "").strip()  # lấy query và xóa khoảng trắng đầu/cuối

    products = Product.objects.filter(product_status=PRODUCT_STATUS_PUBLISHED).order_by("-date")

    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).order_by("-date")
    page_number = request.GET.get("page", DEFAULT_PAGE)
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(page_number)

    context = {
        "products": page_obj,
        "query": query,
        "result_count": products.count(),
        "page_obj": page_obj,
    }
    return render(request, "core/search.html", context)
