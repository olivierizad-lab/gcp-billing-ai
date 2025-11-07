FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (entire backend directory)
COPY . .

# Note: Reasoning engine IDs are automatically discovered from Agent Engine
# No environment variables needed for agent configuration!
# Cloud Run environment variables should be set for:
# - BQ_PROJECT or GCP_PROJECT_ID
# - LOCATION
# - JWT_SECRET_KEY (for authentication)

# Cloud Run expects PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}

