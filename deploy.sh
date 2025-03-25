#!/bin/bash

# Build Docker images for all services
echo "Building Docker image for EnergyCollector..."
docker build -t energycollector-grpc-server:v1 ./src/energycollector/

# Apply Kubernetes manifests for all services
echo "Applying Kubernetes manifests for EnergyCollector..."
kubectl apply -f ./src/energycollector/energycollector-deployment.yaml

echo "All services deployed successfully."