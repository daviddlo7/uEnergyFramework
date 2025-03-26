import grpc, logging
from common.Settings import get_service_host, get_service_port_grpc
from common.Constants import ServiceNameEnum
from energycollector_pb2 import EnergyRequest
from energycollector_pb2_grpc import EnergyCollectorStub

LOGGER = logging.getLogger(__name__)

class EnergyCollectorClient:
    def __init__(self, host=None, port=None):
        """
        Initialize the EnergyCollectorClient with the server address and port.
        """
        if not host:
            host = get_service_host(ServiceNameEnum.ENERGY_COLLECTOR)
        if not port:
            port = get_service_port_grpc(ServiceNameEnum.ENERGY_COLLECTOR)

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
        self.stub = EnergyCollectorStub(self.channel)

    def close(self):
        """
        Close the connection to the gRPC server.
        """
        if self.channel is not None:
            self.channel.close()
            self.channel = None
            self.stub = None

    def run_test(self, device: str) -> str:
        """
        Call the RunTest method on the gRPC server.
        :param device: The device to test (e.g., "HuaweiHL5").
        :return: "Test Started" if successful, or "Error" if something fails.
        """
        try:
            LOGGER.debug(f"RunTest request: {device}")
            request = TestRequest(device=device)
            response = self.stub.RunTest(request)
            LOGGER.debug(f"RunTest result: {response.message}")
            return response.message
        except Exception as e:
            LOGGER.error(f"An error occurred while running the test: {e}")
            return "Error"
