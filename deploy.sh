#!/bin/bash

# Enable essential addons in MicroK8s
microk8s enable dns
microk8s enable storage
microk8s enable ingress

# Apply the namespace configuration
echo "Applying namespace configuration..."
kubectl apply -f namespace.yaml

# Generate gRPC files for all modules
echo "Generating gRPC files for EnergyCollector..."
python3 -m grpc_tools.protoc \
-I./src/energycollector \
--python_out=./src/energycollector \
--grpc_python_out=./src/energycollector \
./src/energycollector/energycollector.proto

echo "Generating gRPC files for Analytics..."
python3 -m grpc_tools.protoc \
-I./src/analytics \
--python_out=./src/analytics \
--grpc_python_out=./src/analytics \
./src/analytics/analytics.proto

echo "Generating gRPC files for WebUI..."
python3 -m grpc_tools.protoc \
-I./src/webui \
--python_out=./src/webui \
--grpc_python_out=./src/webui \
./src/webui/webui.proto

# Build Docker images for all modules (using static tags)
echo "Building Docker image for EnergyCollector..."
docker build -t energycollector:v1 -f ./src/energycollector/Dockerfile .

echo "Building Docker image for Analytics..."
docker build -t analytics:v1 -f ./src/analytics/Dockerfile .

echo "Building Docker image for WebUI..."
docker build -t webui:v1 -f ./src/webui/Dockerfile .

# Export Docker images to tar files for MicroK8s
echo "Exporting Docker image for EnergyCollector to tar file..."
docker save energycollector:v1 -o energycollector-v1.tar

echo "Exporting Docker image for Analytics to tar file..."
docker save analytics:v1 -o analytics-v1.tar

echo "Exporting Docker image for WebUI to tar file..."
docker save webui:v1 -o webui-v1.tar

# Import images into MicroK8s
echo "Importing EnergyCollector image into MicroK8s..."
microk8s ctr image import energycollector-v1.tar

echo "Importing Analytics image into MicroK8s..."
microk8s ctr image import analytics-v1.tar

echo "Importing WebUI image into MicroK8s..."
microk8s ctr image import webui-v1.tar

# Apply Kubernetes manifests for all modules in the namespace uenergyframework
echo "Applying Kubernetes manifests for EnergyCollector..."
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifests for Analytics..."
microk8s kubectl apply -f ./src/analytics/analytics-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifests for WebUI..."
microk8s kubectl apply -f ./src/webui/webui-deployment.yaml -n uenergyframework

# Force a restart of the deployments to ensure changes take effect in the namespace uenergyframework
echo "Restarting deployments to apply changes..."
microk8s kubectl rollout restart deployment energycollector-deployment -n uenergyframework
microk8s kubectl rollout restart deployment analytics-deployment -n uenergyframework
microk8s kubectl rollout restart deployment webui-deployment -n uenergyframework

echo "Deployment completed successfully."
