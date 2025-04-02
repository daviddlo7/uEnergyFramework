# Enable essential addons in MicroK8s
microk8s enable dns
microk8s enable storage
microk8s enable ingress
if ! grep -q "127.0.0.1 uenergyframework.local" /etc/hosts; then
  echo "127.0.0.1 uenergyframework.local" | sudo tee -a /etc/hosts > /dev/null
  echo "Added '127.0.0.1 uenergyframework.local' to /etc/hosts"
else
  echo "'127.0.0.1 uenergyframework.local' is already present in /etc/hosts"
fi

npm install -g protoc-gen-grpc-web