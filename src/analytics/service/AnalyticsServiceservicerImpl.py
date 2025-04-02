import logging
from analytics_pb2 import AnalyticsResponse
from analytics_pb2_grpc import AnalyticsServicer

LOGGER = logging.getLogger(__name__)

class AnalyticsServicerImpl(AnalyticsServicer):
    def CheckConnection(self, request, context):
        """
        Handles the CheckConnection RPC call.

        :param request: The incoming request containing the name of the operation.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            LOGGER.info(f"Received CheckConnection request with name: {request.name}")
            if request.name == "CheckConnection":  # Verifica que el nombre sea válido
                return AnalyticsResponse(message="OK")
            else:
                return AnalyticsResponse(message="Error: Invalid operation name.")
        except Exception as e:
            LOGGER.error(f"An error occurred while handling CheckConnection: {e}")
            return AnalyticsResponse(message="Error")
    def ProcessTestData(self, request, context):
        """
        Handles the ProcessTestData RPC call.

        :param request: The incoming request containing the JSON data as a string.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            LOGGER.info(f"Received ProcessTestData request with data: {request.data}")
            
            if request.data:
                LOGGER.info("Processing test data...")
                self.p
                return AnalyticsResponse(message="OK")
            else:
                return AnalyticsResponse(message="Error: No data provided.")
        except Exception as e:
            LOGGER.error(f"An error occurred while processing test data: {e}")
            return AnalyticsResponse(message="Error")
            