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
            LOGGER.info(f"Received UpdateData request with data: {request.data}")

            if not request.data:
                return UpdateDataResponse(message="Error: Data not provided.")

            # Process the data (example logic)
            processed_data = self.process_data(request.data)

            # Return a response with the processed data
            message = f"Data updated successfully. Processed Data: {processed_data}"
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