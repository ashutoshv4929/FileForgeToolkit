# 1. बेस इमेज: पाइथन 3.12 का उपयोग करें
FROM python:3.12-slim

# 2. सभी जरूरी सिस्टम पैकेज इंस्टॉल करें
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libmagic1 \
    poppler-utils \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 3. वर्किंग डायरेक्टरी सेट करें
WORKDIR /app

# 4. पाइथन पैकेज इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. बाकी एप्लिकेशन कोड कॉपी करें
COPY . .

# 6. ऐप चलाने के लिए कमांड
CMD ["gunicorn", "smart_file_converter.app:app"]
