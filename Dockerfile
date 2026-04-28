# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install dependencies, Go, and required tools
RUN apt-get update && apt-get install -y \
    wget \
    git \
    golang-go \
    && rm -rf /var/lib/apt/lists/*

# Set up Go path
ENV GOPATH /root/go
ENV PATH $GOPATH/bin:$PATH

# Install Subfinder and httpx (ProjectDiscovery)
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Set working directory
WORKDIR /app

# Install Python requests for webhooks
RUN pip install requests

# Copy our ASM script into the container
COPY asm_core.py /app/

# Run the script when the container launches
ENTRYPOINT ["python", "asm_core.py"]
