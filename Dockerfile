FROM python:3.11-slim

WORKDIR /app

# 安装依赖（先复制依赖文件，利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 非 root 用户运行（安全加固）
RUN useradd --create-home --shell /bin/bash apiuser && \
    chown -R apiuser:apiuser /app
USER apiuser

EXPOSE 8000

# 环境变量
ENV API_KEY=change-me-in-production
ENV LOG_LEVEL=INFO
ENV MAX_IMAGE_SIZE_MB=10

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
