#!/bin/bash
kubectl delete all --all -n uenergyframework

# Apply the namespace configuration
echo "Applying namespace configuration..."
kubectl apply -f namespace.yaml

echo "Applying Kubernetes manifest for ingress..."
microk8s kubectl apply -f ingress.yaml

# Generate gRPC files for all modules
echo "Generating gRPC-Web files for EnergyCollector (JavaScript)..."
protoc -I./src/energycollector \
  --js_out=import_style=commonjs:./src/energycollector \
  --grpc-web_out=import_style=commonjs,mode=grpcwebtext:./src/energycollector \
  ./src/energycollector/energycollector.proto

echo "Generating gRPC files for EnergyCollector (Python)..."
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

echo "Building Docker image for WebUI (gRPC)..."
docker build -t webui-grpc:v1 -f ./src/webui/Dockerfile.grpc .

echo "Building Docker image for WebUI (Nginx)..."
docker build -t webui-nginx:v1 -f ./src/webui/Dockerfile.nginx .

# Export Docker images to tar files for MicroK8s
echo "Exporting Docker image for EnergyCollector to tar file..."
docker save energycollector:v1 -o energycollector-v1.tar

echo "Exporting Docker image for Analytics to tar file..."
docker save analytics:v1 -o analytics-v1.tar

echo "Exporting Docker image for WebUI (gRPC) to tar file..."
docker save webui-grpc:v1 -o webui-grpc-v1.tar

echo "Exporting Docker image for WebUI (Nginx) to tar file..."
docker save webui-nginx:v1 -o webui-nginx-v1.tar

# Import images into MicroK8s
echo "Importing EnergyCollector image into MicroK8s..."
microk8s ctr image import energycollector-v1.tar

echo "Importing Analytics image into MicroK8s..."
microk8s ctr image import analytics-v1.tar

echo "Importing WebUI (gRPC) image into MicroK8s..."
microk8s ctr image import webui-grpc-v1.tar

echo "Importing WebUI (Nginx) image into MicroK8s..."
microk8s ctr image import webui-nginx-v1.tar

# Apply Kubernetes manifests for all modules in the namespace uenergyframework
echo "Applying Kubernetes manifests for EnergyCollector..."
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifests for Analytics..."
microk8s kubectl apply -f ./src/analytics/analytics-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifests for WebUI..."
microk8s kubectl apply -f ./src/webui/webui-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifest for InfluxDB..."
microk8s kubectl apply -f ./src/database/database-deployment.yaml -n uenergyframework

echo "Applying Kubernetes manifest for Grafana Dashboard ConfigMap..."
microk8s kubectl apply -f grafana-dashboard-files.yaml -n uenergyframework

echo "Applying Kubernetes manifest for Grafana InfluxDB Connection ConfigMap..."
microk8s kubectl apply -f influxdb-connection-configmap.yaml -n uenergyframework

echo "Applying Kubernetes manifest for Grafana..."
microk8s kubectl apply -f ./src/grafana/grafana-deployment.yaml -n uenergyframework

# Force a restart of the deployments to ensure changes take effect in the namespace uenergyframework
echo "Restarting deployments to apply changes..."
microk8s kubectl rollout restart deployment energycollector-deployment -n uenergyframework
microk8s kubectl rollout restart deployment analytics-deployment -n uenergyframework
microk8s kubectl rollout restart deployment webui-deployment -n uenergyframework
microk8s kubectl rollout restart deployment database-deployment -n uenergyframework
microk8s kubectl rollout restart deployment grafana-deployment -n uenergyframework

echo "Deployment completed successfully."
