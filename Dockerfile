# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install dependencies needed for downloading binaries
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Subfinder
RUN wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.5/subfinder_2.6.5_linux_amd64.zip && \
    unzip subfinder_2.6.5_linux_amd64.zip && \
    mv subfinder /usr/local/bin/ && \
    rm subfinder_2.6.5_linux_amd64.zip

# Install httpx
RUN wget https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_linux_amd64.zip && \
    unzip httpx_1.6.0_linux_amd64.zip && \
    mv httpx /usr/local/bin/ && \
    rm httpx_1.6.0_linux_amd64.zip

# Set working directory
WORKDIR /app

# Install Python requests for webhooks
RUN pip install --no-cache-dir requests

# Copy our ASM script into the container
COPY asm_core.py /app/

# Create the data directory
RUN mkdir -p /app/data

# Run the script
ENTRYPOINT ["python", "asm_core.py"]
