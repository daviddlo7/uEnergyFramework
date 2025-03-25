import logging
import signal
import sys
from service.EnergyCollectorService import EnergyCollectorService

terminate = False
LOGGER: logging.Logger = None

def signal_handler(signal, frame):
    """
    Handles termination signals (e.g., SIGINT, SIGTERM).
    """
    global terminate
    LOGGER.warning("Terminate signal received")
    terminate = True

def main():
    """
    Main function to start the EnergyCollector service.
    """
    global LOGGER

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")
    LOGGER = logging.getLogger("EnergyCollectorMain")

    # Handle termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    LOGGER.info("Starting EnergyCollector service...")

    # Start gRPC service
    grpc_service = EnergyCollectorService()
    grpc_service.start()

    # Wait for termination signal
    while not terminate:
        pass

    LOGGER.info("Terminating EnergyCollector service...")
    grpc_service.stop()
    LOGGER.info("Service stopped successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
