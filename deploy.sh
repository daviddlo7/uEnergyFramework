# Check if images are already in Docker 

    # If not, build images (Dockerfile)


# Deploy (apply) all components (.yaml)

# Build the Docker image for EnergyCollector
echo "Building Docker image for Webui..."
docker build -t website:v1 ./src/webui/
 
# Export the image to a tar file for MicroK8s
echo "Exporting Docker image to tar file..."
docker save website:v1 -o website-v1.tar
 
# Import the image into MicroK8s
echo "Importing image into MicroK8s..."
microk8s ctr image import website-v1.tar
 
# Apply Kubernetes manifests for EnergyCollector in MicroK8s
echo "Applying Kubernetes manifests for Web..."
microk8s kubectl apply -f ./src/webui/DeploymentWeb.yaml
 
 
echo "Deployment completed successfully."
