# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary packages and tools
RUN apt-get update && \
    apt-get install -y clang llvm llvm-cov build-essential libclang-dev && \
    apt-get clean

# Install Python dependencies directly
RUN pip install --no-cache-dir openai python-dotenv

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables
ENV OPENAI_API_KEY=your_openai_api_key_here

# Run the main script when the container launches
CMD ["python", "main.py"]
