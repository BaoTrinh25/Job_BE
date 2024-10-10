# Sử dụng image Python
FROM python:3.12

# Đặt biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Tạo thư mục làm việc
WORKDIR /app

# Cài đặt các gói cần thiết
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    python3-dev \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Sao chép requirements.txt vào container
COPY requirements.txt /app/

# Cập nhật pip và cài đặt các gói từ requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn vào container
COPY . /app

# Expose port
EXPOSE 8000

# Lệnh chạy ứng dụng Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
