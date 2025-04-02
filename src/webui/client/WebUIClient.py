import grpc
import logging

from common.Settings import get_service_host, get_service_port_grpc
from common.Constants import ServiceNameEnum

from webui_pb2 import UpdateDataRequest
from webui_pb2_grpc import WebUIStub

LOGGER = logging.getLogger(__name__)

class WebUIClient:
    def __init__(self, host=None, port=None):
        if not host:
            host = get_service_host(ServiceNameEnum.WEB_UI)
        if not port:
            port = get_service_port_grpc(ServiceNameEnum.WEB_UI)

        self.endpoint = f"{host}:{port}"
        LOGGER.debug(f"Creating channel to {self.endpoint}...")
        self.channel = None
        self.stub = None
        self.connect()
        LOGGER.debug("Channel created")

    def connect(self):
        self.channel = grpc.insecure_channel(self.endpoint)
        self.stub = WebUIStub(self.channel)

    def close(self):
        if self.channel is not None:
            self.channel.close()
            self.channel = None
            self.stub = None