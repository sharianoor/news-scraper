FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Chrome-compatible Chromium and its driver.
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Tell Selenium where Chromium is installed.
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_BIN=/usr/bin/chromium

# Install Python dependencies.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application files.
COPY app.py scraper.py summarizer.py ./

# Make the API port available.
EXPOSE 7000

# Start the API automatically.
CMD ["python", "app.py"]