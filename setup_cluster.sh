# Enable essential addons in MicroK8s
microk8s enable dns
microk8s enable storage
microk8s enable ingress
if ! grep -q "192.168.1.200 webui.uenergyframework database.uenergyframework grafana.uenergyframework" /etc/hosts; then
  echo "192.168.1.200 webui.uenergyframework database.uenergyframework grafana.uenergyframework" | sudo tee -a /etc/hosts > /dev/null
  echo "Added '192.168.1.200 webui.uenergyframework database.uenergyframework grafana.uenergyframework' to /etc/hosts"
else
  echo "'192.168.1.200 webui.uenergyframework database.uenergyframework grafana.uenergyframework' is already present in /etc/hosts"
fi

npm install -g protoc-gen-grpc-web

kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml