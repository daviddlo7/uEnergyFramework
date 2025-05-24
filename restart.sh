microk8s kubectl get crd | grep metallb | awk '{print $1}' | xargs -I {} microk8s kubectl delete crd {}

kubectl delete all --all --all-namespaces

microk8s ctr images ls -q | xargs -r microk8s ctr image remove

docker rm -f $(docker ps -a -q)

docker rmi -f $(docker images -a -q)

microk8s ctr images rm $(microk8s ctr images list -q)

microk8s stop

microk8s start

sudo microk8s reset

for pv in $(kubectl get pv --no-headers | awk '$5=="Released"{print $1}'); do
  kubectl patch pv "$pv" --type=json -p '[{"op": "remove", "path": "/spec/claimRef"}]'
done