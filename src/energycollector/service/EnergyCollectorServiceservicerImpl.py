import logging
import grpc
from energycollector_pb2 import TestResponse
from energycollector_pb2_grpc import EnergyCollectorServicer
from analytics_pb2 import AnalyticsRequest
from analytics_pb2_grpc import AnalyticsStub

LOGGER = logging.getLogger(__name__)

class EnergyCollectorServicerImpl(EnergyCollectorServicer):
    def RunTest(self, request, context):
        try:
            LOGGER.info(f"Received test request for device: {request.device}")

            if not request.device:
                return TestResponse(message="Error: Device not provided.")

            # Call the Analytics service and get the response
            analytics_response = self.call_analytics_service(request.device)

            # Combine responses from EnergyCollector and Analytics services
            message = f"Test Started. Analytics Response: {analytics_response}"
            return TestResponse(message=message)

        except Exception as e:
            LOGGER.error(f"An error occurred while running the test: {e}")
            return TestResponse(message="Error")

    def call_analytics_service(self, name):
        try:
            # Connect to the Analytics service (fixed IP and port)
            channel = grpc.insecure_channel("10.152.183.13:50051")
            stub = AnalyticsStub(channel)

            # Create and send the request to Analytics service
            request = AnalyticsRequest(name=name)
            response = stub.RunAnalytics(request)

            # Close the channel and return the response message
            channel.close()
            return response.message

        except Exception as e:
            LOGGER.error(f"Failed to call Analytics service: {e}")
            return "Error calling Analytics service"
