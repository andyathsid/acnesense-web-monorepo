FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app:create_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Accept build argument for port
ARG FLASK_PORT=8000
ENV FLASK_PORT=${FLASK_PORT}

# Expose port from environment
EXPOSE ${FLASK_PORT}

# Use gunicorn for production with port from environment
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${FLASK_PORT} --worker-tmp-dir /dev/shm --workers 4 --timeout 300 --access-logfile - --error-logfile - 'app:create_app()'"]