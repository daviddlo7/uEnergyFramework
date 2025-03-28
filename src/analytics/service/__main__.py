import logging
import signal
import sys
import threading
import os
from service.AnalyticsService import AnalyticsService

terminate = threading.Event()
LOGGER = None
grpc_service = None

def signal_handler(signal, frame):
    global grpc_service
    LOGGER.warning("Terminate signal received")
    terminate.set()
    if grpc_service:
        grpc_service.stop()

def main():
    global LOGGER, grpc_service
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s",
    )
    LOGGER = logging.getLogger(__name__)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    LOGGER.info("Starting Analytics service...")
    grpc_service = AnalyticsService()
    grpc_service.start()
    while not terminate.wait(timeout=1.0):
        pass
    LOGGER.info("Terminating Analytics service...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
