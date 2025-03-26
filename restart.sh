kubectl delete all --all --all-namespaces

docker rm $(docker ps -a -q)

docker rmi $(docker images -a -q)

microk8s ctr images rm $(microk8s ctr images list -q)

microk8s stop

microk8s start
