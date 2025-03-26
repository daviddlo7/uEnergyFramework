FROM python:3.9-slim

WORKDIR /app/src/energycollector

# Install dependencies listed in requirements.in
COPY requirements.in .
RUN pip install -r requirements.in
RUN pip install protobuf==3.20.3

# Copy all source code into the container
COPY . .

# Expose gRPC port 50051 and Prometheus metrics port (e.g., 8000)
EXPOSE 50051 8000

# Run the main application when the container starts
ENTRYPOINT ["python", "-m", "service.__main__"]