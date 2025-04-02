grpcurl -plaintext -d '{"test_data": "{test_data}"}' 10.152.183.12:50051 energycollector.EnergyCollector/RunTest #&

#Con INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep energycollector-deployment | awk '{print $1}')

#Sin INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep energycollector-deployment | awk '{print $1}') | awk '{sub(/^(INFO|ERROR):[^:]+:/,""); print}'