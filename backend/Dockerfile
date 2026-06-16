FROM python:3.10-slim

# Cài đặt thư viện hệ thống
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc là /app
WORKDIR /app

# Copy requirements trước để tận dụng Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code từ thư mục backend vào /app trong container
# Lúc này cấu trúc bên trong sẽ là: /app/app/...
COPY . .

# THIẾT LẬP PYTHONPATH để Python tìm thấy module 'app'
ENV PYTHONPATH=/app

# Chạy ứng dụng ở cổng 10000 (Render bắt buộc)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]