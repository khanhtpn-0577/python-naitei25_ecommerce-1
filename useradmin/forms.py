from core.models import Product, Coupon
from django import forms
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class AddProductForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _("Product Title"), "class":"form-control"}))
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': _("Product Description"), "class":"form-control"}))
    amount = forms.DecimalField(
        required=True,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'placeholder': _("Sale Price"), 
            'class': "form-control",
            'step': '0.01'
        })
    )
    old_price = forms.DecimalField(
        decimal_places=2,
        max_digits=10,
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': _("0.00"),
            'class': "form-control",
            'step': '0.01',
            'min': '0'
        })
    )
    type = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _("Type of product e.g organic cream"), "class":"form-control"}))
    stock_count = forms.CharField(widget=forms.NumberInput(attrs={'placeholder': _("How many are in stock?"), "class":"form-control"}))
    life = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _("How long would this product live?"), "class":"form-control"}))
    mfd = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'placeholder': _("e.g: 22-11-02"), "class":"form-control"}))
    tags = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _("Tags"), "class":"form-control"}))
    image = forms.ImageField(widget=forms.FileInput(attrs={"class":"form-control"}))

    class Meta:
        model = Product
        fields = [
            'title',
            'image',
            'description',
            'amount',
            'old_price',
            'specifications',
            'type',
            'stock_count',
            'life',
            'mfd',
            'tags',
            'digital',
            'category'
        ]

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError(_("Price must be greater than 0"))
        return amount

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        exclude = ['vendor']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập mã giảm giá (VD: DISCOUNT20)',
                'style': 'text-transform: uppercase;'
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10.0',
                'min': '0',
                'max': '100',
                'step': '0.1'
            }),
            'expiry_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'min_order_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01'
            }),
            'max_discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100.00',
                'min': '0',
                'step': '0.01'
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'apply_once_per_user': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_code(self):
        code = self.cleaned_data['code'].upper().strip()
        if not code:
            raise forms.ValidationError("Mã giảm giá không được để trống.")
        
        if len(code) < 3:
            raise forms.ValidationError("Mã giảm giá phải có ít nhất 3 ký tự.")
        
        # Check for duplicate code
        if self.instance.pk:
            # Editing existing coupon
            if Coupon.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Mã giảm giá này đã tồn tại.")
        else:
            # Creating new coupon
            if Coupon.objects.filter(code=code).exists():
                raise forms.ValidationError("Mã giảm giá này đã tồn tại.")
        return code
    
    def clean_expiry_date(self):
        expiry_date = self.cleaned_data['expiry_date']
        if expiry_date <= timezone.now():
            raise forms.ValidationError("Ngày hết hạn phải lớn hơn thời gian hiện tại.")
        return expiry_date
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is None:
            raise forms.ValidationError("Phần trăm giảm giá không được để trống.")
        if discount < 0:
            raise forms.ValidationError("Phần trăm giảm giá không được âm.")
        if discount > 100:
            raise forms.ValidationError("Phần trăm giảm giá không được vượt quá 100%.")
        return discount
    
    def clean(self):
        cleaned_data = super().clean()
        discount = cleaned_data.get('discount')
        max_discount = cleaned_data.get('max_discount_amount')
        min_order = cleaned_data.get('min_order_amount')
        
        if max_discount and min_order and max_discount > min_order:
            raise forms.ValidationError("Số tiền giảm tối đa không được lớn hơn số tiền đơn hàng tối thiểu.")
        
        return cleaned_data
