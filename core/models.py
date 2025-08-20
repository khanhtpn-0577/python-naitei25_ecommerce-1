from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from django.conf import settings
from taggit.managers import TaggableManager
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.constants import *
from django.contrib.auth.models import AbstractUser
from userauths.models import User
from . import constants as C
from django.core.exceptions import ObjectDoesNotExist
# Create your models here.
def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    mobile = models.CharField(max_length=C.MAX_LENGTH_MOBILE , null=True, blank=True)
    address = models.CharField(max_length=C.MAX_LENGTH_ADDRESS, null=True, blank=True)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'address'
        verbose_name = "Address"
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.user} - {self.address}"

class Image(models.Model):
    image =  CloudinaryField('image')
    alt_text = models.CharField(max_length=C.MAX_LENGTH_TEXT , null=True, blank=True)
    object_type = models.CharField(max_length=C.MAX_LENGTH_OBJECT_TYPE, choices=C.OBJECT_TYPE_CHOICES )  # e.g., 'Product', 'Category', 'Vendor'
    object_id = models.CharField(max_length=C.MAX_LENGTH_OBJECT_ID)    # e.g., pid, cid, vid
    is_primary = models.BooleanField(default=False)
    image_type = models.CharField(max_length=C.MAX_LENGTH_IMAGE_TYPE , null=True, blank=True)  # thumbnail, cover, etc.
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'image'
        verbose_name = "Image"
        verbose_name_plural = "Images"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.object_type} - {self.object_id}"

class Vendor(models.Model):
    vid = models.CharField(max_length=C.MAX_LENGTH_VID, primary_key=True)
    title = models.CharField(max_length=C.MAX_LENGTH_TITLE)
    description = models.TextField()
    address = models.CharField(max_length=C.MAX_LENGTH_ADDRESS)
    contact = models.CharField(max_length=C.MAX_LENGTH_CONTACT)
    chat_resp_time = models.PositiveIntegerField(help_text="Thời gian phản hồi (phút)")
    shipping_on_time = models.PositiveIntegerField(
        help_text="Tỷ lệ giao hàng đúng hẹn (%)",
        validators=[MinValueValidator(C.MIN), MaxValueValidator(C.SHIP_ON_TIME )]
    )

    authentic_rating = models.FloatField(
        help_text="Điểm đánh giá độ tin cậy, 0.0-5.0",
        validators=[MinValueValidator(C.MIN), MaxValueValidator(C.AUTHENTIC_RATING)]
    )

    days_return = models.PositiveIntegerField(
        help_text="Số ngày cho phép hoàn trả",
        validators=[MinValueValidator(C.MIN), MaxValueValidator(C.DAY_RETURN)]  # giới hạn trong 2 tháng
    )

    warranty_period = models.PositiveIntegerField(
        help_text="Thời gian bảo hành (tháng)",
        validators=[MinValueValidator(C.MIN), MaxValueValidator(C.WARRANTY_PERIOD_TIME_MONTH )]  # tối đa 5 năm
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (ID: {self.vid})"

    @property
    def image_set(self):
        """Get all images for this vendor"""
        return Image.objects.filter(object_type='Vendor', object_id=self.vid)

    @property
    def banner_set(self):
        """Get all banner images for this vendor"""
        return Image.objects.filter(object_type='vendor_banner', object_id=self.vid)
    
    @property
    def primary_image(self):
        """Get primary image for this vendor"""
        return Image.objects.filter(object_type='Vendor', object_id=self.vid, is_primary=True).first()
    
    @property
    def primary_banner(self):
        """Get primary banner image for this vendor"""
        return Image.objects.filter(object_type='vendor_banner', object_id=self.vid, is_primary=True).first()

    @property
    def primary_image_url(self):
        """Get primary image URL for this vendor"""
        img = self.primary_image
        if img:
            try:
                return img.image.url
            except Exception as e:
                print(f"Error getting image URL for vendor {self.vid}: {e}")
                return None
        return '/static/assets/imgs/vendor/vendor-placeholder.jpg'

    @property
    def primary_banner_url(self):
        """Get primary banner image URL"""
        img = self.primary_banner
        if img:
            try:
                return img.image.url
            except Exception as e:
                print(f"Error getting banner URL for vendor {self.vid}: {e}")
                return None
        return '/static/assets/imgs/vendor/vendor-banner-placeholder.jpg'
    
    def get_default_image_url(self):
        """Get default image URL if no primary image exists"""
        return '/static/assets/imgs/vendor/vendor-placeholder.jpg'
    
    def get_default_banner_url(self):
        """Get default banner URL if no primary banner exists"""
        return '/static/assets/imgs/vendor/vendor-banner-placeholder.jpg'
    
    @property
    def display_image_url(self):
        """Get primary image URL or default if not exists"""
        return self.primary_image_url or self.get_default_image_url()
    
    @property
    def display_banner_url(self):
        """Get primary banner URL or default if not exists"""
        return self.primary_banner_url or self.get_default_banner_url()
    
    def add_image(self, image, alt_text=None, is_primary=False):
        """Add a new image for this vendor"""
        # Set all existing images as non-primary if this one is primary
        if is_primary:
            Image.objects.filter(object_type='Vendor', object_id=self.vid, is_primary=True).update(is_primary=False)
        
        # Create new image
        return Image.objects.create(
            url=image,
            alt_text=alt_text or self.title,
            object_type='Vendor',
            object_id=self.vid,
            is_primary=is_primary
        )
    
    def add_banner(self, image, alt_text=None, is_primary=False):
        """Add a new banner image for this vendor"""
        # Set all existing banner images as non-primary if this one is primary
        if is_primary:
            Image.objects.filter(object_type='vendor_banner', object_id=self.vid, is_primary=True).update(is_primary=False)
        
        # Create new banner image
        return Image.objects.create(
            url=image,
            alt_text=alt_text or f"{self.title} Banner",
            object_type='vendor_banner',
            object_id=self.vid,
            is_primary=is_primary
        )
    
    def set_primary_image(self, image_id):
        """Set an existing image as primary"""
        # First, unset all primary images
        Image.objects.filter(object_type='Vendor', object_id=self.vid, is_primary=True).update(is_primary=False)
        
        # Then set the selected image as primary
        return Image.objects.filter(id=image_id, object_type='Vendor', object_id=self.vid).update(is_primary=True)
    
    def set_primary_banner(self, image_id):
        """Set an existing banner as primary"""
        # First, unset all primary banners
        Image.objects.filter(object_type='vendor_banner', object_id=self.vid, is_primary=True).update(is_primary=False)
        
        # Then set the selected banner as primary
        return Image.objects.filter(id=image_id, object_type='vendor_banner', object_id=self.vid).update(is_primary=True)

    class Meta:
        db_table = 'vendor'
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"


    @property
    def primary_image(self):
        return Image.objects.filter(object_type='Vendor', object_id=self.vid, is_primary=True).first()

    # Lấy URL ảnh chính
    @property
    def primary_image_url(self):
        img = self.primary_image
        if img:
            try:
                return img.image.url  # CloudinaryField object
            except Exception as e:
                print(f"Error getting image URL for vendor {self.vid}: {e}")
                return None
        return '/static/assets/imgs/default.jpg'


class Coupon(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    code = models.CharField(max_length=C.MAX_LENGTH_CODE , unique=True)
    discount = models.FloatField()
    active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField()
    min_order_amount = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2)
    apply_once_per_user = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.vendor.title}"

    class Meta:
        db_table = 'coupon'
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

class CouponUser(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user} - {self.coupon.code}"
    class Meta:
        db_table = 'coupon_user'
        constraints = [
            models.UniqueConstraint(fields=['coupon', 'user'], name='unique_coupon_user')
        ]

class Category(models.Model):
    cid = models.CharField(max_length=C.MAX_LENGTH_CID, primary_key=True)
    title = models.CharField(max_length=C.MAX_LENGTH_TITLE)

    # Self-referencing ForeignKey
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )

    def __str__(self):
        if self.parent:
            return f"{self.parent.title} ➝ {self.title}"
        return self.title

    @property
    def image_set(self):
        """Get all images for this category"""
        return Image.objects.filter(object_type='Category', object_id=self.cid)
    
    @property
    def primary_image(self):
        """Get primary image for this category"""
        return Image.objects.filter(object_type='Category', object_id=self.cid, is_primary=True).first()
    
    @property
    def primary_image_url(self):
        """Get primary image URL for this category"""
        img = self.primary_image
        if img:
            try:
                return img.image.url  # CloudinaryField
            except Exception as e:
                print(f"Error getting image URL for category {self.cid}: {e}")
                return None
        return None
    
    @property
    def display_image_url(self):
        """Get primary image URL or default"""
        return self.primary_image_url or '/static/assets/imgs/shop/cat-1.png'

    class Meta:
        db_table = 'category'
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        
    def get_primary_image(self):
        """Trả về đối tượng Image chính (primary)."""
        return Image.objects.filter(
            object_type='Category',
            object_id=self.cid,
            is_primary=True
        ).first()
    @property
    def primary_image_url(self):
        """Trả về URL của ảnh chính (nếu có)."""
        image = self.get_primary_image()
        if image:
            return image.image.url.replace("http://", "https://")
        return '/static/assets/imgs/default.jpg'

class Product(models.Model):
    pid = ShortUUIDField(unique=True, length=10, max_length=C.MAX_LENGTH_PID , alphabet="abcdefgh12345", primary_key=True)

    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, related_name="products"
    )
    vendor = models.ForeignKey(
        'Vendor', on_delete=models.SET_NULL, null=True, related_name="products"
    )
    title = models.CharField(max_length=C.MAX_LENGTH_TITLE)
    description = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2, default=0.00)
    old_price = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2, default=0.00)
    specifications = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=C.MAX_LENGTH_TYPE, null=True, blank=True)
    stock_count = models.CharField(max_length=C.MAX_LENGTH_STOCK_COUNT , null=True, blank=True)
    life = models.CharField(max_length=C.MAX_LENGTH_LIFE, null=True, blank=True)
    mfd = models.DateTimeField(null=True, blank=True)
    product_status = models.CharField(
        max_length=C.MAX_LENGTH_PRODUCT_STATUS,
        choices=C.PRODUCT_STATUS_CHOICES,
        default='in_review'
    )
    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)
    sku = ShortUUIDField(unique=True, length=4, max_length=C.MAX_LENGTH_SKU, prefix="sku", alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    rating_avg = models.FloatField(default=0.0)

    def __repr__(self):
        return f"{self.title} (ID: {self.pid})"

    @property
    def image_set(self):
        """Get all images for this product"""
        return Image.objects.filter(object_type='product', object_id=self.pid)

    def get_precentage(self):
        """Calculate discount percentage"""
        if self.old_price and self.old_price > 0:
            return ((self.old_price - self.amount) / self.old_price) * 100
        return 0

    class Meta:
        db_table = 'product'
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-date']
    def __repr__(self):
        return f"<Product {self.title}>"


    def __repr__(self):
        return f"<Product {self.title}>"
    def get_precentage(self):
        """
        Trả về phần trăm giảm giá: (old_price - amount) / old_price * 100
        Làm tròn đến 0 chữ số thập phân.
        """
        try:
            if self.old_price > 0:
                return round((self.old_price - self.amount) / self.old_price * 100, 0)
            return 0
        except:
            return 0
    def get_primary_image(self):
        """Trả về đối tượng Image chính (primary)."""
        return Image.objects.filter(
            object_type='Product',
            object_id=self.pid,
            is_primary=True
        ).first()
    @property
    def primary_image_url(self):
        """Trả về URL của ảnh chính (nếu có)."""
        image = self.get_primary_image()
        if image:
            return image.image.url.replace("http://", "https://")
        return DEFAULT_CATEGORY_IMAGE
    @property
    def additional_images(self):
        return Image.objects.filter(
            object_type='Product',
            object_id=self.pid,
            is_primary=False
        )




class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="reviews")
    review = models.TextField()
    rating = models.IntegerField(choices=C.RATING, default=None)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_review"
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.product} ({self.rating}★)"
    def get_primary_image(self):
        """Trả về đối tượng Image chính (primary)."""
        return Image.objects.filter(
            object_type='Product',
            object_id=self.pid,
            is_primary=True
        ).first()
    @property
    def primary_image_url(self):
        """Trả về URL của ảnh chính (nếu có)."""
        image = self.get_primary_image()
        if image:
            return image.image.url.replace("http://", "https://")
        return '/static/assets/imgs/default.jpg'

class ReturnRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    order_product = models.ForeignKey('CartOrderProducts', on_delete=models.CASCADE, related_name='return_requests')
    reason = models.TextField()
    status = models.CharField(max_length=C.MAX_LENGTH_RETRUNRQ_STATUS, choices=C.RETURN_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else "Unknown User"
        return f"ReturnRequest #{self.pk} - {username}"

    class Meta:
        db_table = 'return_request'
        verbose_name = "Return Request"
        verbose_name_plural = "Return Requests"
        ordering = ['-created_at']

class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_orders")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="cart_orders")
    amount = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="cart_orders")
    paid_status = models.BooleanField(default=False)
    order_status = models.CharField(
        max_length=C.MAX_LENGTH_ORDER_STATUS,
        choices=C.ORDER_STATUS_CHOICES,
        default='processing'
    )
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} - {self.user.username}"

    class Meta:
        db_table = 'cart_order'
        verbose_name = "Cart Order"
        verbose_name_plural = "Cart Orders"
        ordering = ['-order_date']

class CartOrderProducts(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name='order_products')
    item = models.CharField(max_length=C.MAX_LENGTH_ITEM)
    image = models.TextField(max_length=C.MAX_LENGTH_IMAGE_URL)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2)
    total = models.DecimalField(max_digits=C.MAX_DIGITS_AMOUNT, decimal_places=2)

    def __str__(self):
        return f"{self.item} (x{self.qty})"
    
    @property
    def image_src(self):
        if not self.image:
            return ""
        img = self.image.strip()
        # Trả thẳng nếu là URL tuyệt đối hoặc data URI
        if img.startswith(("http://", "https://", "data:")):
            return img
        # Còn lại coi là đường dẫn trong MEDIA
        return f"{settings.MEDIA_URL}{img.lstrip('/')}"
    class Meta:
        db_table = 'cart_order_products'
        verbose_name = "Cart Order Product"
        verbose_name_plural = "Cart Order Products"
        ordering = ['-id']

