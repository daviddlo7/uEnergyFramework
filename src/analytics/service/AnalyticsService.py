import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
import os
import logging

from analytics_pb2_grpc import add_AnalyticsServiceServicer_to_server
from analytics_pb2 import DESCRIPTOR as ANALYTICS_DESCRIPTOR
from service.AnalyticsServiceservicerImpl import AnalyticsServiceServicerImpl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRPC_MAX_WORKERS = 10

class AnalyticsService:
    def __init__(self):
        self.port = os.getenv("GRPC_PORT", "50051")
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=GRPC_MAX_WORKERS))
        self.servicer = AnalyticsServiceServicerImpl()

    def install_servicers(self):
        add_AnalyticsServiceServicer_to_server(self.servicer, self.server)
        service_names = [
            ANALYTICS_DESCRIPTOR.services_by_name["AnalyticsService"].full_name,
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self.server)

    def start(self):
        try:
            self.install_servicers()
            self.server.add_insecure_port(f"[::]:{self.port}")
            logger.info(f"Analytics server running on port {self.port}...")
            self.server.start()
            self.server.wait_for_termination()
        except Exception as e:
            logger.error(f"Error starting Analytics server: {e}")

    def stop(self):
        try:
            logger.info("Stopping Analytics server...")
            self.server.stop(0)
        except Exception as e:
            logger.error(f"Error stopping Analytics server: {e}")
