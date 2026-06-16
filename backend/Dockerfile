FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết (bao gồm cả Tesseract OCR cho Python xử lý ảnh)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy file requirements cũ của bạn vào để cài đặt gói thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn của thư mục backend vào trong Docker container
COPY . .

# Khởi chạy ứng dụng FastAPI bằng Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]