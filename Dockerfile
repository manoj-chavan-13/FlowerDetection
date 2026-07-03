# Use official Python lightweight runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_PORT=5000 \
    FLASK_DEBUG=False

# Create a non-root user and group for security best practices
RUN groupadd -r florasense && useradd -r -g florasense florasense

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definition file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies without cache to keep image slim
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py index.html script.js style.css ./

# Change ownership of the app directory to non-root user
RUN chown -R florasense:florasense /app

# Switch to non-root user
USER florasense

# Expose port 5000 for web traffic
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
