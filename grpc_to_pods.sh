grpcurl -plaintext 10.152.183.11:50051 list
grpcurl -plaintext 10.152.183.12:50051 list
grpcurl -plaintext 10.152.183.13:50051 list
grpcurl -plaintext 10.152.183.11:50051 describe webui.WebUI
grpcurl -plaintext 10.152.183.12:50051 describe energycollector.EnergyCollector
grpcurl -plaintext 10.152.183.13:50051 describe analytics.Analytics
grpcurl -plaintext -d '{"data": "example_data"}' 10.152.183.11:50051 webui.WebUI/UpdateData
grpcurl -plaintext -d '{"device": "example_device"}' 10.152.183.12:50051 energycollector.EnergyCollector/RunTest
grpcurl -plaintext -d '{"name": "example_name"}' 10.152.183.13:50051 analytics.Analytics/RunAnalytics