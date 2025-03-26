import logging
import signal
import sys
import threading
import os

from service.EnergyCollectorService import EnergyCollectorService

terminate = threading.Event()
LOGGER = None
grpc_service = None  # Global variable for the gRPC service

def signal_handler(signal, frame):  # pylint: disable=redefined-outer-name
    global grpc_service  # pylint: disable=global-statement
    LOGGER.warning("Terminate signal received")
    terminate.set()
    if grpc_service:
        grpc_service.stop()  # Detener el servidor gRPC

def main():
    global LOGGER, grpc_service  # pylint: disable=global-statement

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s",
    )
    LOGGER = logging.getLogger(__name__)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    LOGGER.info("Starting EnergyCollector service...")

    # Start gRPC service
    grpc_service = EnergyCollectorService()
    grpc_service.start()

    # Wait for Ctrl+C or termination signal
    while not terminate.wait(timeout=1.0):
        pass

    LOGGER.info("Terminating EnergyCollector service...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
