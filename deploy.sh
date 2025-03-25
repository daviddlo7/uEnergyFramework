#!/bin/bash

# Build the Docker image for EnergyCollector
echo "Building Docker image for EnergyCollector..."
docker build -t energycollector-grpc-server ./src/energycollector/

# Apply Kubernetes manifests for EnergyCollector
echo "Applying Kubernetes manifests for EnergyCollector..."
kubectl apply -f ./k8s/energycollector-deployment.yaml
kubectl apply -f ./k8s/energycollector-service-grpc.yaml

echo "EnergyCollector deployment completed."