import logging
from energycollector_pb2 import EnergyResponse
from energycollector_pb2_grpc import EnergyCollectorServicer

LOGGER = logging.getLogger(__name__)

class EnergyCollectorServicerImpl(EnergyCollectorServicer):
    def RunTest(self, request, context):
        """
        Handles the RunTest RPC call.
        :param request: The incoming request containing the device.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            LOGGER.info(f"Received test request for device: {request.device}")
            if request.device:  # Verifica que se haya especificado un dispositivo
                return TestResponse(message="Test Started")
            else:
                return TestResponse(message="Error")
        except Exception as e:
            LOGGER.error(f"An error occurred while running the test: {e}")
            return TestResponse(message="Error")