#Terminal 1 -> EnergyCollector Logs

#Con INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep energycollector-deployment | awk '{print $1}')

#Sin INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep energycollector-deployment | awk '{print $1}') | awk '{sub(/^(INFO|ERROR):[^:]+:/,""); print}'

#Terminal 2 -> Analytics Logs

#Con INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep analytics-deployment | awk '{print $1}')

#Sin INFO o ERROR
kubectl logs -f -n uenergyframework $(kubectl get pods -n uenergyframework --no-headers | grep analytics-deployment | awk '{print $1}') | awk '{sub(/^(INFO|ERROR):[^:]+:/,""); print}'

# Terminal 3 -> Run Test gRPC EnergyCollector

grpcurl -plaintext -d '{"test_data": "{test_data}"}' 10.152.183.12:50051 energycollector.EnergyCollector/RunTest

# Run test 2 with TestParameters
grpcurl -plaintext -d '{
  "devices_names": ["HL4_5_1_Huawei"],
  "traffic_configuration": "IDLE",
  "escenario": "huawei",
  "total_time": 1,
  "traffic_change": 0,
  "traffic": 0,
  "packet_change": 0,
  "packet_size": 0,
  "db": "pruebas",
  "web_interface": false,
  "debug_mode": false,
  "save_csvs": false
}' 10.152.183.12:50051 energycollector.EnergyCollector/RunTest2

# WebUI grpcurl examples
# TestStatus
grpcurl -plaintext -d '{"test_status": "Started"}' 10.152.183.11:50051 webui.WebUi/TestStatus

# Process Data
grpcurl -plaintext -d '{"devices_data": "Huawei: 500W"}' 10.152.183.11:50051 webui.WebUi/UpdateData
