FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run a script to download and pull the model when container starts
RUN echo '#!/bin/bash\n\
echo "Waiting for Ollama service to be ready..."\n\
until curl -s http://ollama:11434/api/tags > /dev/null; do\n\
  sleep 5\n\
done\n\
echo "Pulling qwen2:7b model..."\n\
curl -X POST http://ollama:11434/api/pull -d "{\"model\":\"qwen2:7b\"}"\n\
echo "Model pulled. Starting Flask application..."\n\
gunicorn --bind 0.0.0.0:8000 --timeout 300 --workers 2 --threads 4 --worker-tmp-dir /dev/shm run:app' > /app/start.sh

RUN chmod +x /app/start.sh

# Use gunicorn as the production WSGI server
CMD ["/app/start.sh"]