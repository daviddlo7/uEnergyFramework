import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
from proto.energycollector_pb2_grpc import add_EnergyCollectorServicer_to_server
from service.EnergyCollectorServiceservicerImpl import EnergyCollectorServicerImpl
from proto.energycollector_pb2 import DESCRIPTOR as ENERGYCOLLECTOR_DESCRIPTOR

# Custom gRPC settings
GRPC_MAX_WORKERS = 10

class EnergyCollectorService:
    def __init__(self):
        self.port = "50051"
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=GRPC_MAX_WORKERS))
        self.servicer = EnergyCollectorServicerImpl()

    def install_servicers(self):
        add_EnergyCollectorServicer_to_server(self.servicer, self.server)

        # Habilitar reflexión
        service_names = [
            ENERGYCOLLECTOR_DESCRIPTOR.services_by_name["EnergyCollector"].full_name,
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self.server)

    def start(self):
        self.install_servicers()
        self.server.add_insecure_port(f"[::]:{self.port}")
        print(f"EnergyCollector server running on port {self.port}...")
        self.server.start()
        self.server.wait_for_termination()

    def stop(self):
        print("Stopping EnergyCollector server...")
        self.server.stop(0)
