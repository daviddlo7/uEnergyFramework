#!/bin/bash

set -e

# Variables con rutas absolutas (ajusta si es necesario)
BASE_DIR="$(pwd)"
ENERGYCOLLECTOR_TAR="$BASE_DIR/energycollector-v1.tar"
ANALYTICS_TAR="$BASE_DIR/analytics-v1.tar"
WEBUI_GRPC_TAR="$BASE_DIR/webui-grpc-v1.tar"
WEBUI_NGINX_TAR="$BASE_DIR/webui-nginx-v1.tar"

kubectl delete all --all -n uenergyframework || true

echo "Applying namespace configuration..."
kubectl apply -f src/namespace.yaml

echo "Applying Kubernetes manifest for ingress..."
microk8s kubectl apply -f src/ingress.yaml

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

echo "Building Docker image for EnergyCollector..."
docker build -t energycollector:v1 -f ./src/energycollector/Dockerfile .

echo "Building Docker image for Analytics..."
docker build -t analytics:v1 -f ./src/analytics/Dockerfile .

echo "Building Docker image for WebUI (gRPC)..."
docker build -t webui-grpc:v1 -f ./src/webui/Dockerfile.grpc .

echo "Building Docker image for WebUI (Nginx)..."
docker build -t webui-nginx:v1 -f ./src/webui/Dockerfile.nginx .

echo "Saving Docker images to tar files..."
docker save energycollector:v1 -o "$ENERGYCOLLECTOR_TAR"
docker save analytics:v1 -o "$ANALYTICS_TAR"
docker save webui-grpc:v1 -o "$WEBUI_GRPC_TAR"
docker save webui-nginx:v1 -o "$WEBUI_NGINX_TAR"

echo "Importing images into MicroK8s..."

if ! microk8s ctr image import "$ENERGYCOLLECTOR_TAR"; then
  echo "Error importing EnergyCollector image"; exit 1
fi

if ! microk8s ctr image import "$ANALYTICS_TAR"; then
  echo "Error importing Analytics image"; exit 1
fi

if ! microk8s ctr image import "$WEBUI_GRPC_TAR"; then
  echo "Error importing WebUI (gRPC) image"; exit 1
fi

if ! microk8s ctr image import "$WEBUI_NGINX_TAR"; then
  echo "Error importing WebUI (Nginx) image"; exit 1
fi

echo "Verifying imported images:"
microk8s ctr images ls | grep -E 'energycollector|analytics|webui'

echo "Applying Kubernetes manifests..."
microk8s kubectl apply -f src/configmap-uenergyframework.yaml -n uenergyframework
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml -n uenergyframework
microk8s kubectl apply -f ./src/analytics/analytics-deployment.yaml -n uenergyframework
microk8s kubectl apply -f ./src/webui/webui-deployment.yaml -n uenergyframework
microk8s kubectl apply -f ./src/database/database-deployment.yaml -n uenergyframework
microk8s kubectl apply -f ./src/grafana/grafana-deployment.yaml -n uenergyframework

echo "Restarting deployments..."
microk8s kubectl rollout restart deployment energycollector-deployment -n uenergyframework
microk8s kubectl rollout restart deployment analytics-deployment -n uenergyframework
microk8s kubectl rollout restart deployment webui-deployment -n uenergyframework
microk8s kubectl rollout restart deployment database-deployment -n uenergyframework
microk8s kubectl rollout restart deployment grafana-deployment -n uenergyframework

echo "Deployment completed successfully."
