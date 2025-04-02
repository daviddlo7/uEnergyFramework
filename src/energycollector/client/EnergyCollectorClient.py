import grpc

from common.Settings import get_service_host, get_service_port_grpc
from common.Constants import ServiceNameEnum

from energycollector_pb2 import TestRequest
from energycollector_pb2_grpc import EnergyCollectorStub

import logging
logger = logging.getLogger(__name__)

class EnergyCollectorClient:
    def __init__(self, host=None, port=None):
        if not host:
            host = get_service_host(ServiceNameEnum.ENERGY_COLLECTOR)
        if not port:
            port = get_service_port_grpc(ServiceNameEnum.ENERGY_COLLECTOR)

        self.endpoint = f"{host}:{port}"
        logger.debug(f"Creating channel to {self.endpoint}...")
        self.channel = None
        self.stub = None
        self.connect()
        logger.debug("Channel created")

    def connect(self):
        self.channel = grpc.insecure_channel(self.endpoint)
        self.stub = EnergyCollectorStub(self.channel)

    def close(self):
        if self.channel is not None:
            self.channel.close()
            self.channel = None
            self.stub = None