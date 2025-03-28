import grpc
import logging

from common.Settings import get_service_host, get_service_port_grpc
from common.Constants import ServiceNameEnum

from analytics_pb2 import AnalyticsRequest
from analytics_pb2_grpc import AnalyticsStub

LOGGER = logging.getLogger(__name__)

class AnalyticsClient:
    def __init__(self, host=None, port=None):
        """
        Initialize the AnalyticsClient with the server address and port.
        """
        if not host:
            host = get_service_host(ServiceNameEnum.ANALYTICS)
        if not port:
            port = get_service_port_grpc(ServiceNameEnum.ANALYTICS)
        
        self.endpoint = f"{host}:{port}"
        LOGGER.debug(f"Creating channel to {self.endpoint}...")
        
        self.channel = None
        self.stub = None
        self.connect()
        LOGGER.debug("Channel created")

    def connect(self):
        """
        Establish a connection to the gRPC server.
        """
        self.channel = grpc.insecure_channel(self.endpoint)
        self.stub = AnalyticsStub(self.channel)

    def close(self):
        """
        Close the connection to the gRPC server.
        """
        if self.channel is not None:
            self.channel.close()
            self.channel = None
            self.stub = None

    def run_analytics(self, name: str) -> str:
        """
        Call the RunAnalytics method on the gRPC server.

        :param name: The name of the analytics operation.
        :return: Response message indicating success or error.
        """
        try:
            LOGGER.debug(f"RunAnalytics request: {name}")
            request = AnalyticsRequest(name=name)
            response = self.stub.RunAnalytics(request)
            LOGGER.debug(f"RunAnalytics result: {response.message}")
            return response.message
        except Exception as e:
            LOGGER.error(f"An error occurred while running analytics: {e}")
            return "Error"
