FROM python:3.11-slim

WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     libgl1-mesa-glx \
#     libglib2.0-0 \
#     && rm -rf /var/lib/apt/lists/*

# Install OpenCV headless first
RUN pip install --no-cache-dir opencv-python-headless

# Copy requirements first for better caching
COPY requirements.txt .

# Install other requirements after
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app:create_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Accept build argument for port
ARG FLASK_PORT=5000
ENV FLASK_PORT=${FLASK_PORT}

# Expose port from environment
EXPOSE ${FLASK_PORT}

# Use gunicorn for production with port from environment
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${FLASK_PORT} --worker-tmp-dir /dev/shm --workers 4 --timeout 300 --access-logfile - --error-logfile - 'app:create_app()'"]