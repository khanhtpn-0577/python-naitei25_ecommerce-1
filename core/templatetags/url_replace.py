# core/templatetags/url_replace.py

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """
    Template tag này dùng để thay thế hoặc thêm các tham số GET trong URL hiện tại.
    """
    # Lấy một bản sao của các tham số GET hiện tại từ request
    query = context['request'].GET.copy()
    
    # Cập nhật bản sao với các tham số mới được truyền vào tag
    for key, value in kwargs.items():
        query[key] = value
        
    # Trả về chuỗi query đã được mã hóa để dùng trong URL
    return query.urlencode()