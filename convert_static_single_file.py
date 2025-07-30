import re

def convert_static_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Thêm {% load static %} nếu chưa có
    if '{% load static %}' not in content:
        content = '{% load static %}\n' + content

    # Pattern: tìm src="assets/..." hoặc href="assets/..."
    pattern = r'''(src|href)=["'](assets/[^"']+)["']'''

    # Hàm thay thế bằng cú pháp {% static '...' %}
    def replace_func(match):
        attr = match.group(1)
        path = match.group(2)
        return f'{attr}="{{% static \'{path}\' %}}"'

    # Áp dụng thay thế
    new_content = re.sub(pattern, replace_func, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Đã chuyển đổi: {file_path}")

# === CONFIG HERE ===
file_path = "templates/core/index.html"  # Đổi nếu cần

# === RUN ===
convert_static_in_file(file_path)
