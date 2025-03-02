# Use an official lightweight Python image.
FROM python:3.11-slim

# Install git.
RUN apt-get update && apt-get install -y git

# Set environment variables.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory.
WORKDIR /app

# Copy requirements file.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of the application.
COPY . .

# Expose port (adjust if needed).
EXPOSE 8000

# Run the FastAPI application via uvicorn.
CMD ["uvicorn", "src.api.endpoints:app", "--host", "0.0.0.0", "--port", "8000"]