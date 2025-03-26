import logging
from proto.energycollector_pb2 import EnergyResponse
from proto.energycollector_pb2_grpc import EnergyCollectorServicer

LOGGER = logging.getLogger(__name__)

class EnergyCollectorServicerImpl(EnergyCollectorServicer):
    def CollectEnergy(self, request, context):
        """
        Handles the CollectEnergy RPC call.
        
        :param request: The incoming request containing the energy source.
        :param context: The gRPC context.
        :return: A response message indicating success.
        """
        LOGGER.info(f"Received energy collection request from source: {request.source}")
        response_message = f"Energy collected from {request.source}"
        return EnergyResponse(message=response_message)