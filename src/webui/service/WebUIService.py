import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
import os
import logging
from webui_pb2_grpc import add_WebUIServicer_to_server
from webui_pb2 import DESCRIPTOR as WEBUI_DESCRIPTOR
from service.WebUIServiceservicerImpl import WebUIServicerImpl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom gRPC settings
GRPC_MAX_WORKERS = 10

class WebUIService:
    """
    WebUIService implements a gRPC server for the WebUI service.
    """

    def __init__(self):
        """
        Initializes the gRPC server and the service implementation.
        """
        self.port = os.getenv("GRPC_PORT", "50052")  # Default port for WebUI service
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=GRPC_MAX_WORKERS))
        self.servicer = WebUIServicerImpl()  # Service implementation

    def install_servicers(self):
        """
        Registers the service implementation and enables reflection.
        """
        add_WebUIServicer_to_server(self.servicer, self.server)

        # Enable reflection for debugging tools like grpcurl
        service_names = [
            WEBUI_DESCRIPTOR.services_by_name["WebUI"].full_name,
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self.server)

    def start(self):
        """
        Starts the gRPC server and waits for termination.
        """
        try:
            self.install_servicers()
            self.server.add_insecure_port(f"[::]:{self.port}")
            logger.info(f"WebUI server running on port {self.port}...")
            self.server.start()
            self.server.wait_for_termination()
        except Exception as e:
            logger.error(f"Error starting WebUI server: {e}")

    def stop(self):
        """
        Stops the gRPC server gracefully.
        """
        try:
            logger.info("Stopping WebUI server...")
            self.server.stop(0)
        except Exception as e:
            logger.error(f"Error stopping WebUI server: {e}")
