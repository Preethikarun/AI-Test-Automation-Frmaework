# Use the official Playwright image — has Python + Chromium pre-installed
# No apt-get needed — all browser dependencies already included
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
# requirements.txt copied first — Docker caches this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy framework code
COPY . .

# Environment variables
ENV PYTHONPATH=/app

# Default command — run all tests
CMD ["pytest", "tests/", "-v", "--tb=short"]