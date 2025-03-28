#!/bin/bash

# Activar complementos esenciales en MicroK8s
microk8s enable dns
microk8s enable storage
microk8s enable ingress

# Generar archivos gRPC para todos los módulos
echo "Generando archivos gRPC para EnergyCollector..."
python3 -m grpc_tools.protoc \
-I./src/energycollector \
--python_out=./src/energycollector \
--grpc_python_out=./src/energycollector \
./src/energycollector/energycollector.proto

echo "Generando archivos gRPC para Analytics..."
python3 -m grpc_tools.protoc \
-I./src/analytics \
--python_out=./src/analytics \
--grpc_python_out=./src/analytics \
./src/analytics/analytics.proto

echo "Generando archivos gRPC para WebUI..."
python3 -m grpc_tools.protoc \
-I./src/webui \
--python_out=./src/webui \
--grpc_python_out=./src/webui \
./src/webui/webui.proto

# Construir imágenes Docker para todos los módulos
echo "Construyendo imagen Docker para EnergyCollector..."
docker build -t energycollector:v1 -f ./src/energycollector/Dockerfile .

echo "Construyendo imagen Docker para Analytics..."
docker build -t analytics:v1 -f ./src/analytics/Dockerfile .

echo "Construyendo imagen Docker para WebUI..."
docker build -t webui:v1 -f ./src/webui/Dockerfile .

# Exportar imágenes Docker a archivos tar para MicroK8s
echo "Exportando imagen Docker de EnergyCollector a archivo tar..."
docker save energycollector:v1 -o energycollector-v1.tar

echo "Exportando imagen Docker de Analytics a archivo tar..."
docker save analytics:v1 -o analytics-v1.tar

echo "Exportando imagen Docker de WebUI a archivo tar..."
docker save webui:v1 -o webui-v1.tar

# Importar las imágenes en MicroK8s
echo "Importando imagen de EnergyCollector en MicroK8s..."
microk8s ctr image import energycollector-v1.tar

echo "Importando imagen de Analytics en MicroK8s..."
microk8s ctr image import analytics-v1.tar

echo "Importando imagen de WebUI en MicroK8s..."
microk8s ctr image import webui-v1.tar

# Aplicar los manifiestos de Kubernetes para todos los módulos
echo "Aplicando manifiestos de Kubernetes para EnergyCollector..."
microk8s kubectl apply -f ./src/energycollector/energycollector-deployment.yaml

echo "Aplicando manifiestos de Kubernetes para Analytics..."
microk8s kubectl apply -f ./src/analytics/analytics-deployment.yaml

echo "Aplicando manifiestos de Kubernetes para WebUI..."
microk8s kubectl apply -f ./src/webui/webui-deployment.yaml

echo "Despliegue completado exitosamente."
