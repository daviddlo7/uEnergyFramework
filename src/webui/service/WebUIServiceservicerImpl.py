import logging
from webui_pb2 import UpdateDataResponse
from webui_pb2_grpc import WebUIServicer

LOGGER = logging.getLogger(__name__)

class WebUIServicerImpl(WebUIServicer):
    def UpdateData(self, request, context):
    """
    Handles the UpdateData gRPC request.
    """
    try:
        LOGGER.info(f"Received Devices Data: {request.data}")

        if not request.data:
            return UpdateDataResponse(message="Error: Data not provided.")

        # Process test status
        devices_data = request.data #Started, Error, Finished
        #data = process_data(data) # Return data string with format
        # Mandar device_data por el websocket

        message = f"Data updated successfully. Processed Data: {devices_data}"
        return UpdateDataResponse(message=message)

    except Exception as e:
        LOGGER.error(f"An error occurred while updating data: {e}")
        return UpdateDataResponse(message="Error")
    def ShowGui(self, request, context):
        """
        Handles the UpdateData gRPC request.
        """
        try:
            LOGGER.info(f"Received UpdateData request with data: {request.data}")

            if not request.data:
                return UpdateDataResponse(message="Error: Data not provided.")

            processed_data = self.show_gui(request.data)

            message = f"Data updated successfully. Processed Data: {processed_data}"
            return UpdateDataResponse(message=message)

        except Exception as e:
            LOGGER.error(f"An error occurred while updating data: {e}")
            return UpdateDataResponse(message="Error")
    def TestStatus(self, request, context):
    """
    Handles the UpdateData gRPC request.
    """
    try:
        LOGGER.info(f"Received Test Status: {request.data}")

        if not request.data:
            return UpdateDataResponse(message="Error: Test Status not provided.")

        # Process test status
        test_status = request.data #Started, Error, Finished
        # Mandar test_status por el websocket

        message = f"Data updated successfully. Processed Data: {test_status}"
        return UpdateDataResponse(message=message)

    except Exception as e:
        LOGGER.error(f"An error occurred while updating data: {e}")
        return UpdateDataResponse(message="Error")
    def process_data(self, data):
        """
        Example method to process the received data.
        """
        try:
            LOGGER.debug(f"Processing data: {data}")
            # Add your custom logic here (e.g., transformation, validation, etc.)
            processed_data = data.upper()  # Example: Convert to uppercase
            return processed_data

        except Exception as e:
            LOGGER.error(f"Error processing data: {e}")
            return "Error processing data"
    def show_gui(self, data):

        # Add GUI Funcionality

        return 0