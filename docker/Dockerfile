# =========================================================================
# Dockerfile - Cloud-Native Smart Warehouse Application
# Cloud Computing Unit 3: Containerization vs Virtualization
# =========================================================================

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment variables for production cloud container
ENV PYTHONUNBUFFERED=1 \
    PORT=5000 \
    HOST=0.0.0.0 \
    ENVIRONMENT=Docker

# Expose web service port
EXPOSE 5000

# Container healthcheck (Cloud-Native Liveness Probe)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch application via production WSGI server
CMD ["python", "run_server.py"]
