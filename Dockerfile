# Use the official Playwright image — has Python + Chromium pre-installed
# No apt-get needed — all browser dependencies already included
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

# Set working directory
WORKDIR /app

FROM python:3.11-slim

# Install Node.js 20 (for Playwright MCP server)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @playwright/mcp@latest

# Rest of Python setup unchanged
COPY requirements.txt .
RUN pip install --break-system-packages -r requirements.txt
COPY . .

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