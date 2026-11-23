FROM python:3.12-slim

# Install Tesseract OCR and Poppler (required for scanning images & scanned PDFs)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies using pre-built binary wheels for faster builds
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefer-binary --default-timeout=1000 --retries 10 --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
