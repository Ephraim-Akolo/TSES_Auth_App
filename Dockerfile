# Use official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

