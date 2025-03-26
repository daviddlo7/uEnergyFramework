# Activating DNS
microk8s enable dns

# Generate gRPC files from the .proto definition
echo "Generating gRPC files..."
python3 -m grpc_tools.protoc \
    -I./src/energycollector \
    --python_out=./src/energycollector \
    --grpc_python_out=./src/energycollector \
    ./src/energycollector/energycollector.proto

# Build the Docker image for EnergyCollector
echo "Building Docker image for EnergyCollector..."
docker build -t energycollector:v1 ./src/energycollector/

echo "Building Docker image for Webui..."
docker build -t webui:v1 ./src/webui/

# Export the image to a tar file for MicroK8s
echo "Exporting EnergyCollector Docker image to tar file..."
docker save energycollector:v1 -o energycollector-v1.tar

echo "Exporting Webui Docker image to tar file..."
docker save webui:v1 -o webui-v1.tar

# Import the image into MicroK8s
echo "Importing EnergyCollector image into MicroK8s..."
microk8s ctr image import energycollector-v1.tar

echo "Importing Webui image into MicroK8s..."
microk8s ctr image import webui-v1.tar

# Apply Kubernetes manifests for EnergyCollector in MicroK8s
echo "Applying Kubernetes manifests for EnergyCollector..."
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml

echo "Applying Kubernetes manifests for Web..."
microk8s kubectl apply -f ./src/webui/webui-deployment.yaml

echo "Deployment completed successfully."

