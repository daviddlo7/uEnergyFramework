import grpc
from concurrent import futures
import energycollector_pb2_grpc
from service.EnergyCollectorServiceservicerImpl import EnergyCollectorServicer

def serve():
    """
    Starts the gRPC server for the EnergyCollector service.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    energycollector_pb2_grpc.add_EnergyCollectorServicer_to_server(EnergyCollectorServicer(), server)
    server.add_insecure_port('[::]:50051')  # Listen on port 50051
    print("EnergyCollector server running on port 50051...")
    server.start()
    server.wait_for_termination()
