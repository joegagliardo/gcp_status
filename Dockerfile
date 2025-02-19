# Use a suitable base image 
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements.txt first to leverage Docker's caching
COPY requirements.txt .

# Install dependencies (within the container)
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY gcp_helpers.py /app
COPY main.py /app
COPY config.json /app
COPY templates /app/templates

# Set the entry point (the command to run when the container starts)
CMD ["python3", "main.py"]

# docker build -t joegagliardo/gcp_helpers .
# docker run -v /Users/joey/Dev/gcp_status:/gcp_status --name gcp_status -p8080:8080 -e GOOGLE_APPLICATION_CREDENTIALS="/gcp_status/surfn-peru-gcp-status.json" joegagliardo/gcp_status


# docker run --name gcp_status -p 8080:8080 -v /Users/joey/Dev/gcp_status:/app -e GOOGLE_APPLICATION_CREDENTIALS=/app/surfn-peru-gcp-status.json joegagliardo/gcp_status