# Activating DNS
microk8s enable dns

# Generate gRPC files from the .proto definition
echo "Generating gRPC files..."
python3 -m grpc_tools.protoc \
    -I./src/energycollector/proto \
    --python_out=./src/energycollector/proto \
    --grpc_python_out=./src/energycollector/proto \
    ./src/energycollector/proto/energycollector.proto

# Build the Docker image for EnergyCollector
<<<<<<< HEAD
echo "Building Docker image for EnergyCollector..."
docker build -t energycollector:v1 ./src/energycollector/

echo "Building Docker image for Webui..."
docker build -t website:v1 ./src/webui/

# Export the image to a tar file for MicroK8s
echo "Exporting Docker image to tar file..."
docker save energycollector:v1 -o energycollector-v1.tar

echo "Exporting Docker image to tar file..."
docker save website:v1 -o website-v1.tar

# Import the image into MicroK8s
echo "Importing image into MicroK8s..."
microk8s ctr image import energycollector-v1.tar

echo "Importing image into MicroK8s..."
microk8s ctr image import website-v1.tar

# Apply Kubernetes manifests for EnergyCollector in MicroK8s
echo "Applying Kubernetes manifests for EnergyCollector..."
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml

echo "Applying Kubernetes manifests for Web..."
microk8s kubectl apply -f ./src/webui/DeploymentWeb.yaml


echo "Deployment completed successfully."
