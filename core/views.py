from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from .models import Product
from django.template.loader import render_to_string
from django.db.models import Avg, Count
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
from taggit.models import Tag
from core.constants import *
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.shortcuts import render
from .models import Product, Image
from core.forms import ProductReviewForm
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import transaction
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.db.models import Min, Max
from django.db.models.functions import ExtractMonth
from userauths.models import *
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
import calendar


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
        updated_cart_data = {}

        for p_id, item in request.session['cart_data_obj'].items():
            try:
                product = Product.objects.get(pid=p_id)
                price = float(item.get('price', product.amount) or 0)
                qty = int(item.get('qty', 1))
                subtotal = qty * price
            except Product.DoesNotExist:
                messages.warning(request, _("Product with ID %(pid)s is no longer available.") % {"pid": p_id})
                continue
            except (ValueError, TypeError):
                price = 0
                qty = 0
                subtotal = 0

            item['subtotal'] = subtotal
            cart_items[p_id] = item
            updated_cart_data[p_id] = item
            cart_total_amount += subtotal

        # Cập nhật lại session giỏ hàng
        request.session['cart_data_obj'] = updated_cart_data

        # Nếu giỏ rỗng sau khi lọc -> return luôn, tránh StopIteration
        if not cart_items:
            messages.warning(request, _("Your cart is empty"))
            return redirect("core:index")

        # Lấy vendor từ sản phẩm đầu tiên
        first_product_id = next(iter(cart_items))
        product = Product.objects.get(pid=first_product_id)
        vendor = product.vendor

        # Tạo hoặc cập nhật đơn hàng
        order, created = CartOrder.objects.get_or_create(
            user=request.user,
            order_status='processing',
            defaults={
                "vendor": vendor,
                "amount": Decimal(cart_total_amount)
            }
        )
        if not created:
            order.amount = Decimal(cart_total_amount)
            order.save()

        return render(request, "core/cart.html", {
            "cart_data": cart_items,
            'totalcartitems': len(cart_items),
            'cart_total_amount': cart_total_amount,
            'order': order
        })

    messages.warning(request, _("Your cart is empty"))
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

def about_us(request):
    return render(request, "core/about_us.html")
@login_required
def customer_dashboard(request):
    CART_STATUS = 'processing'

    # Base queryset cho user hiện tại (tối ưu join)
    base_qs = (
        CartOrder.objects
        .filter(user=request.user)
        .select_related('vendor')
        .prefetch_related('order_products')
    )

    # Giỏ hàng (đơn ở trạng thái processing)
    carts_list = base_qs.filter(order_status=CART_STATUS).order_by('-order_date')

    # Đơn hàng đã chốt (không phải processing)
    orders_list = base_qs.exclude(order_status=CART_STATUS).order_by('-order_date')

    # Địa chỉ của user
    address_list = Address.objects.filter(user=request.user).order_by('-id')

    # Thống kê số đơn hàng (đÃ CHỐT) theo tháng
    monthly = (
        base_qs.exclude(order_status=CART_STATUS)
        .annotate(month=ExtractMonth('order_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    month = []
    total_orders = []
    for row in monthly:
        # row['month'] có thể là None nếu DB trả về kỳ lạ; an toàn thêm check
        m = row['month']
        if m:
            month.append(calendar.month_name[m])
            total_orders.append(row['count'])

    # Xử lý thêm địa chỉ
    if request.method == "POST":
        addr_text = request.POST.get("address", "").strip()
        mobile = request.POST.get("mobile", "").strip()

        if not addr_text or not mobile:
            messages.error(request, "Vui lòng nhập đầy đủ địa chỉ và số điện thoại.")
        else:
            Address.objects.create(
                user=request.user,
                address=addr_text,
                mobile=mobile,
            )
            messages.success(request, "Đã thêm địa chỉ thành công.")
        return redirect("core:dashboard")

    # Hồ sơ user (an toàn tránh DoesNotExist)
    user_profile = Profile.objects.filter(user=request.user).first()

    context = {
        "user_profile": user_profile,
        # Danh sách
        "carts_list": carts_list,           # giỏ hàng (processing)
        "orders_list": orders_list,         # đơn hàng đã chốt
        "address_list": address_list,
        # Thống kê
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, 'core/dashboard.html', context)
@login_required
@require_http_methods(["GET", "POST"])
def make_address_default(request):
    addr_id = request.GET.get("id") or request.POST.get("id")
    if not addr_id:
        return JsonResponse({"boolean": False, "msg": "missing id"}, status=400)

    try:
        with transaction.atomic():
            # Chỉ cập nhật trong phạm vi user hiện tại
            Address.objects.filter(user=request.user, status=True).update(status=False)
            addr = Address.objects.select_for_update().get(id=addr_id, user=request.user)
            addr.status = True
            addr.save(update_fields=["status"])
    except Address.DoesNotExist:
        return JsonResponse({"boolean": False, "msg": "not found"}, status=404)

    return JsonResponse({"boolean": True, "id": int(addr_id)})

def search_view(request):
    return render(request, "core/search.html")
def apply_coupon_to_order(request, order, code, subtotal):
    """
    Xử lý logic áp dụng coupon cho một order.
    """
    code = code.strip()
    try:
        coupon = Coupon.objects.get(code__iexact=code, active=True)

        # Hết hạn
        if coupon.expiry_date < timezone.now():
            messages.warning(request, _("Coupon has expired."))
        elif subtotal < coupon.min_order_amount:
            messages.warning(
                request,
                _("Minimum order amount should be $%(amount)s") % {"amount": coupon.min_order_amount}
            )
        elif order.coupon == coupon and coupon.apply_once_per_user:
            messages.warning(request, _("You have already applied this coupon."))
        else:
            order.coupon = coupon
            order.save()
            messages.success(
                request,
                _("Coupon '%(code)s' applied successfully.") % {"code": coupon.code}
            )
    except Coupon.DoesNotExist:
        messages.error(request, _("Invalid coupon code."))

def checkout(request, oid):
    order = get_object_or_404(CartOrder, id=oid, user=request.user)
    with transaction.atomic():
      if order.coupon:
        order.coupon = None
        order.save()
        messages.info(request,_("Cart changed. Coupon has been removed."))
      # Xóa toàn bộ sản phẩm cũ của order (nếu có)
      CartOrderProducts.objects.filter(order=order).delete()

      # Tạo lại CartOrderProducts từ session
      cart = request.session.get('cart_data_obj', {})
      for pid, item in cart.items():
          try:
              product = Product.objects.get(pid=pid)
              qty = int(item.get('qty', 1))
              price = Decimal(str(item.get('price', 0)))
              CartOrderProducts.objects.create(
                  order=order,
                  item=product.title,
                  image=product.primary_image_url,
                  qty=qty,
                  price=price,
                  total=qty * price
              )
          except Product.DoesNotExist:
              messages.warning(request,("Some products in your cart are no longer available and have been removed."))
              continue

      # Tính toán giá
      order_items = CartOrderProducts.objects.filter(order=order)
      subtotal = sum([i.total for i in order_items])
      tax = Decimal('0')
      shipping = Decimal('0')
      discount = Decimal('0')
      total = subtotal

      # Xử lý áp dụng coupon
      if request.method == "POST" and "apply_coupon" in request.POST:
          code = request.POST.get("code", "").strip()
          try:
              coupon = Coupon.objects.get(code__iexact=code, active=True)
              apply_coupon_to_order(request, order, code, subtotal)
          except Coupon.DoesNotExist:
              messages.error(request,  _("Invalid coupon code."))

      # Tính lại tổng nếu có coupon
      if order.coupon:
          coupon = order.coupon
          discount = subtotal * Decimal(str(coupon.discount)) / Decimal('100')
          if discount > coupon.max_discount_amount:
              discount = coupon.max_discount_amount
          total = subtotal - discount + tax + shipping
          order.amount = total
          order.save()
    host = request.get_host()
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': subtotal,
        'item_name': "Order-Item-No-" + str(order.id),
        'invoice': "INVOICE_NO-3",
        'currency_code': "USD",
        'notify_url': 'http://{}/{}'.format(host, reverse("core:paypal-ipn")),
        'return_url': 'http://{}/{}'.format(host, reverse("core:payment-completed")),
        'cancel_url': 'http://{}/{}'.format(host, reverse("core:payment-failed")),
    }
    paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

    context = {
      "order": order,
      "order_items": order_items,
      "subtotal": subtotal,
      "tax": tax,
      "shipping": shipping,
      "discount": discount,
      "total": total,
      "payment_button_form": paypal_payment_button,
    }
    return render(request, "core/checkout.html", context)

@login_required
def payment_completed_view(request, oid):
    order = CartOrder.objects.get(oid=oid)

    if order.paid_status == False:
        order.paid_status = True
        order.order_status = 'shipped'
        order.save()

    context = {
        "order": order,
    }
    return render(request, 'core/payment-completed.html',  context)

def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')

def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderProducts.objects.filter(order=order)
    context = {
        "order_items": order_items,
    }
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
    related_products = Product.objects.filter(category=product.category).exclude(pid=pid)[:4]
    address = None
    if request.user.is_authenticated:
        address = Address.objects.filter(user=request.user).first()

    reviews = ProductReview.objects.filter(product=product).order_by("-date")
    reviews_with_width = []
    for r in reviews:
        width = r.rating * 20
        reviews_with_width.append((r, width))

    reviews = ProductReview.objects.filter(product=product).order_by("-date")
    reviews_with_width = []
    for r in reviews:
        width = r.rating * 20
        reviews_with_width.append((r, width))

    # average review
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))
    rating_counts = get_rating_counts(product)

    #product review form
    review_form = ProductReviewForm()

    make_review = True

    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()

        if user_review_count > 0:
            make_review = False
    context = {
        "p": product,
        "address": address,
        "related_products": related_products,
        "reviews": reviews,
        "average_rating": average_rating,
        "reviews_with_width": reviews_with_width,
        "rating_counts": rating_counts,
        "review_form": review_form,
        "make_review": make_review
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

def get_rating_counts(product):
    # Đếm số lượng review theo từng mức rating
    queryset = ProductReview.objects.filter(product=product).values('rating').annotate(count=Count('id'))
    rating_dict = {item['rating']: item['count'] for item in queryset}
    results = []
    for value, stars in RATING:
        results.append({
            'rating': value,
            'stars': stars,
            'count': rating_dict.get(value, 0)
        })
    return results

def _to_decimal(v):
    if v in (None, ""): 
        return None
    try:
        return Decimal(str(v).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None

def _getlist(request, name):
    # hỗ trợ cả name và name[] (tùy frontend gửi)
    return request.GET.getlist(f"{name}[]") or request.GET.getlist(name)

def build_products_qs(request):
    """Trả về queryset đã áp dụng các filter từ URL."""
    categories = _getlist(request, "category")
    vendors    = _getlist(request, "vendor")
    min_price  = _to_decimal(request.GET.get("min_price"))
    max_price  = _to_decimal(request.GET.get("max_price"))

    qs = Product.objects.filter(product_status="published")

    if min_price is not None:
        qs = qs.filter(amount__gte=min_price)
    if max_price is not None:
        qs = qs.filter(amount__lte=max_price)
    if categories:
        qs = qs.filter(category_id__in=categories)
    if vendors:
        qs = qs.filter(vendor_id__in=vendors)

    return qs.select_related("category", "vendor").order_by("-pid")
# --------------------------------

def product_list_view(request):
    # dữ liệu cho sidebar/filter
    tags = Tag.objects.all().order_by("-id")[:TAG_LIMIT]
    categories_all = Category.objects.all()
    vendors_all = Vendor.objects.all()
    min_max_price = Product.objects.aggregate(Min("amount"), Max("amount"))

    # áp dụng filter từ URL
    qs = build_products_qs(request)

    # phân trang
    try:
        page_number = int(request.GET.get("page", DEFAULT_PAGE))
    except (TypeError, ValueError):
        page_number = DEFAULT_PAGE
    try:
        per_page = int(request.GET.get("per_page", PRODUCTS_PER_PAGE))
    except (TypeError, ValueError):
        per_page = PRODUCTS_PER_PAGE

    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(page_number)

    context = {
        "products": page_obj,          # Page object, lặp trong template được
        "page_obj": page_obj,
        "tags": tags,
        "categories": categories_all,
        "vendors": vendors_all,
        "min_max_price": min_max_price,   # dùng {{ min_max_price.amount__min }} / {{ ...max }}
    }
    return render(request, "core/product-list.html", context)


def filter_product(request):
    # Dùng chung logic lọc
    qs = build_products_qs(request)

    # phân trang (nếu frontend truyền)
    try:
        page_number = int(request.GET.get("page", DEFAULT_PAGE))
    except (TypeError, ValueError):
        page_number = DEFAULT_PAGE
    try:
        per_page = int(request.GET.get("per_page", PRODUCTS_PER_PAGE))
    except (TypeError, ValueError):
        per_page = PRODUCTS_PER_PAGE

    paginator = Paginator(qs, per_page)
    page_obj  = paginator.get_page(page_number)

    # render partial (nhớ truyền request để giữ query cho pagination)
    html = render_to_string(
        "core/async/product-list.html",
        {"products": page_obj, "page_obj": page_obj},
        request=request,
    )

    return JsonResponse({
        "data": html,
        "count": paginator.count,
        "page": page_obj.number,
        "has_next": page_obj.has_next(),
        "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
    })


@require_POST
@login_required
def cod_checkout(request):
    """
    Người dùng chọn COD:
    - Giữ amount đã tính sẵn trong order
    - Đặt order_status='shipped'
    - paid_status=False (chưa thu tiền)
    - Xoá giỏ trong session
    - Điều hướng sang trang chi tiết COD
    """
    oid = request.POST.get("oid")
    order = get_object_or_404(CartOrder, id=oid, user=request.user)

    # Đảm bảo có item
    if not order.order_products.exists():
        messages.error(request, _("Your cart is empty or order has no items."))
        return redirect("core:cart")

    # Nếu vì lý do gì đó amount chưa set, tính lại nhanh từ dòng hàng
    if not order.amount or order.amount <= 0:
        amt = order.order_products.aggregate(total=Sum('total'))['total'] or Decimal("0")
        order.amount = amt.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Cập nhật trạng thái COD theo yêu cầu
    order.paid_status = False
    order.order_status = 'shipped'   # <-- theo yêu cầu
    order.save(update_fields=["amount", "paid_status", "order_status"])

    # Xoá giỏ + dấu băng nếu có
    request.session['cart_data_obj'] = {}
    request.session.pop('frozen_order_id', None)
    request.session.modified = True

    return redirect("core:cod-detail", oid=order.id)


@login_required
def cod_detail(request, oid):
    """
    Màn hình chi tiết đơn COD (hoá đơn rút gọn) + nút Accept
    """
    order = get_object_or_404(CartOrder, id=oid, user=request.user)
    items = order.order_products.all()
    order_items = CartOrderProducts.objects.filter(order=order)
    subtotal = sum([i.total for i in order_items])
    discount = Decimal('0.00')
    if order.coupon:
      coupon = order.coupon
      discount = subtotal * Decimal(str(coupon.discount)) / Decimal('100')
      if discount > coupon.max_discount_amount:
        discount = coupon.max_discount_amount
    return render(request, "core/cod_detail.html", {
        "order": order,
        "order_items": items,
        "discount": discount,
    })


@require_POST
@login_required
def cod_accept(request, oid):
    """
    Người dùng xác nhận đã nhận hàng (Accept):
    - Đánh dấu order_status='completed'
    - Tuỳ yêu cầu nghiệp vụ: coi như đã thu tiền -> paid_status=True
    """
    order = get_object_or_404(CartOrder, id=oid, user=request.user)

    order.order_status = 'shipped'
    order.paid_status = False
    order.save(update_fields=["order_status", "paid_status"])

    messages.success(request, _("Thanks! Your COD order is completed."))
    # Điều hướng đến trang lịch sử đơn hàng (đổi route cho phù hợp dự án của bạn)
    return redirect("core:orders")
@login_required
def order_list(request):
    orders = CartOrder.objects.filter(user=request.user).order_by('-order_date')
    return render(request, "core/order_list.html", {"orders": orders})
