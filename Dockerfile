FROM python:3.11-slim

WORKDIR /code

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create HF cache directory with permissive rights for cloud container runtimes
ENV HF_HOME=/code/.cache/huggingface
RUN mkdir -p /code/.cache/huggingface && chmod -R 777 /code/.cache

# Copy application files
COPY . /code

# Port configuration (Standard for Docker deployment)
EXPOSE 8000

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
