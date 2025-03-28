import logging
from analytics_pb2 import AnalyticsResponse
from analytics_pb2_grpc import AnalyticsServicer

LOGGER = logging.getLogger(__name__)

class AnalyticsServicerImpl(AnalyticsServicer):
    def RunAnalytics(self, request, context):
        """
        Handles the RunAnalytics RPC call.

        :param request: The incoming request containing the name of the operation.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            LOGGER.info(f"Received analytics request for operation: {request.name}")
            if request.name:  # Verifica que se haya especificado un nombre
                return AnalyticsResponse(message=f"Analytics operation '{request.name}' started successfully.")
            else:
                return AnalyticsResponse(message="Error: Operation name not provided.")
        except Exception as e:
            LOGGER.error(f"An error occurred while running analytics: {e}")
            return AnalyticsResponse(message="Error")
