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
# COPY config.json /app
COPY templates /app/templates

# Set the entry point (the command to run when the container starts)
CMD python3 main.py


