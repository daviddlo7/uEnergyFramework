import logging
from analytics_pb2 import AnalyticsResponse
from analytics_pb2_grpc import AnalyticsServiceServicer
import math
import numpy as np
from scipy.stats import t
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

default_logger = logging.getLogger("defaultLogger")
default_logger.setLevel(logging.INFO)

logger_cli = logging.getLogger("logger_cli")
logger_cli.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s') 
handler.setFormatter(formatter)
logger_cli.addHandler(handler)
logger_cli.propagate = False

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
for handler in root_logger.handlers:
    handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s:%(message)s'))

class AnalyticsServiceServicerImpl(AnalyticsServiceServicer):
    def __init__(self):
        self.analytics = Analytics()


    def CheckConnection(self, request, context):
        """
        Handles the CheckConnection RPC call.

        :param request: The incoming request containing the name of the operation.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            logger_cli.info(f"Received CheckConnection request with name: {request.id}")
            if request.id == "CheckConnection":  # Verifica que el nombre sea válido
                return AnalyticsResponse(message="OK")
            else:
                return AnalyticsResponse(message="Error: Invalid operation name.")
        except Exception as e:
            logger_cli.error(f"An error occurred while handling CheckConnection: {e}")
            return AnalyticsResponse(message="Error")

    def ProcessTestData(self, request, context):
        """
        Handles the ProcessTestData RPC call.

        :param request: The incoming request containing test parameters.
        :param context: The gRPC context.
        :return: A response message indicating success or error.
        """
        try:
            # Convert Protobuf object to a Python dictionary
            def convert_to_dict(proto_obj):
                """
                Recursively converts a Protobuf object to a Python dictionary.
                """
                if isinstance(proto_obj, dict):
                    return {k: convert_to_dict(v) for k, v in proto_obj.items()}
                elif isinstance(proto_obj, list):
                    return [convert_to_dict(v) for v in proto_obj]
                elif hasattr(proto_obj, "ListFields"):
                    return {field.name: convert_to_dict(getattr(proto_obj, field.name)) for field in
                            proto_obj.DESCRIPTOR.fields}
                else:
                    return proto_obj

            # Extract device name and test parameters
            device_name = request.device_name
            test_parameters = convert_to_dict(request.test_parameters)

            logger_cli.error(f"DATOS TEST PARAMETERS: {test_parameters}")

            # Call the analytics function with the converted dictionary
            self.analytics.process_test_data_influxdb(device_name, test_parameters)

            # Return success response
            return AnalyticsResponse(message="OK")

        except Exception as e:
            logger_cli.error(f"An error occurred while processing test data: {e}")
            return AnalyticsResponse(message="Error")

class Analytics:
    """
    Class that implements the Analytics module, will be in charge of extracting the statistics of the test and with
    them to complete the corresponding Excels. On demand, it will also be able to analyse the data from the dynamic
    database to obtain the static data.

    Attributes:
        telemetry_stats (dict): Test statistics.
    """

    def __init__(self):
        self.time_series_db = AnalyticsTimeSeriesDB()
        self.analytics_db = AnalyticsTelemetryDB()
        self.static_db = AnalyticsStaticDB()
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.time_series_bucket = "time_series_db_pruebas"
        self.telemetry_bucket = "telemetry_db_pruebas"
        self.static_bucket = "static_db_pruebas"

    def test_statistics(self, test_data, test_parameters, all_components):
        times_values = []
        n_intervalos = 1

        components_data = {component: [] for component in all_components}
        components_dict = {component: {} for component in all_components}
        test_statistics = {
            'Name': test_parameters.device_name,
            'Configuration': test_parameters.configuration,
            'Traffic Test': test_parameters.traffic_configuration,
            'Start Date': test_parameters.start_date,
            'Start Time': test_parameters.start_time
        }

        start_time = None

        if test_parameters.traffic_change is None and test_parameters.packet_change is None:
            interval = test_parameters.max_interval * test_parameters.interval
        else:
            if test_parameters.traffic_change is None:
                interval = test_parameters.packet_change
            elif test_parameters.packet_change is None:
                interval = test_parameters.traffic_change
            else:
                interval = min(test_parameters.traffic_change, test_parameters.packet_change)

        for key in test_data.keys():
            record = test_data[key]
            times_value = float(record["Times_s"])
            times_values.append(times_value)

            for data in components_data:
                if data == 'Device':
                    components_data[data].append(float(record['InstantaneousPower_Device_W']))
                else:
                    components_data[data].append(float(record[data]))
            if start_time is None:
                start_time = times_value

            if max(times_values) + test_parameters.interval > interval * n_intervalos or key == len(
                    test_data.keys()) - 1:
                if max(times_values) > interval * test_parameters.max_interval:
                    break
                start_interval = round((math.floor(times_values[0] / interval) * interval) / 60, 2)
                end_interval = round((math.ceil(times_values[-1] / interval) * interval) / 60, 2)
                interval_key = f"{start_interval}-{end_interval}"
                nivel_significativo = 0.05

                for data in components_data:
                    values = components_data[data]
                    if len(values) != 0:
                        avg_value = float(np.mean(values))
                        std_value = float(np.std(values))
                        min_value = float(np.min(values))
                        max_value = float(np.max(values))
                        n = float(len(values))
                        dof = n - 1

                        t_value = t.ppf(1 - nivel_significativo / 2, dof)
                        margin_error = float(t_value * (std_value / np.sqrt(n)))

                        if interval_key not in test_statistics:
                            test_statistics[interval_key] = {}

                        # Ahora añadir el nuevo valor bajo la clave data
                        test_statistics[interval_key][data] = {
                            "Average": round(avg_value, 2),
                            "Min": round(min_value, 2),
                            "Max": round(max_value, 2),
                            "Sample Size": n,  # El tamaño de la muestra no necesita redondeo
                            "Standard Deviation": round(std_value, 2),
                            "Margin of Error (95% CI)": round(margin_error, 2),
                            "Confidence Interval (95%)": f"{round(avg_value, 2):.2f} +- {round(margin_error, 2):.2f}"
                        }

                    else:
                        test_statistics[data][interval_key] = {
                            "Average": None,
                            "Min": None,
                            "Max": None,
                            "Sample Size": None,
                            "Standard Deviation": None,
                            "Margin of Error (95% CI)": None,
                            "Confidence Interval (95%)": None
                        }

                times_values = []
                for data in components_data:
                    components_data[data] = []
                n_intervalos += 1
                components_data = {component: [] for component in all_components}

        return test_statistics

    def test_statistics_influxdb(self, device_name, test_data, test_parameters, all_components):
        times_values = []
        n_intervalos = 1

        components_data = {component: [] for component in all_components}
        components_dict = {component: {} for component in all_components}
        test_statistics = {
            'Name': device_name,
            'Configuration': test_parameters.configuration[device_name],
            'Traffic Test': test_parameters.traffic_configuration,
            'Start Date': test_parameters.start_date,
            'Start Time': test_parameters.start_time
        }

        start_time = None

        if test_parameters.traffic_change is None and test_parameters.packet_change is None:
            interval = test_parameters.max_interval * test_parameters.interval
        else:
            if test_parameters.traffic_change is None:
                interval = test_parameters.packet_change
            elif test_parameters.packet_change is None:
                interval = test_parameters.traffic_change
            else:
                interval = min(test_parameters.traffic_change, test_parameters.packet_change)

        for key in test_data.keys():
            record = test_data[key]
            times_value = float(record["Times"])
            times_values.append(times_value)

            for data in components_data:
                if data == 'Device':
                    components_data[data].append(float(record['power_device']))
                else:
                    components_data[data].append(float(record[data]))
            if start_time is None:
                start_time = times_value

            if max(times_values) > interval * n_intervalos or key == len(test_data.keys()) - 1:
                if max(times_values) > interval * test_parameters.max_interval:
                    break
                start_interval = round((math.floor(times_values[0] / interval) * interval) / 60, 2)
                end_interval = round((math.ceil(times_values[-1] / interval) * interval) / 60, 2)
                interval_key = f"{start_interval}-{end_interval}"

                if interval_key not in test_statistics:
                    try:
                        test_statistics[interval_key] = {
                            "StartTime": start_interval,
                            "EndTime": end_interval,
                            "Time Interval": f"{start_interval}-{end_interval}",
                            "Traffic": test_parameters.traffic if test_parameters.traffic_change is None else
                            test_parameters.traffic[n_intervalos - 1],
                            "PacketSize": test_parameters.packet_size if test_parameters.packet_change is None else
                            test_parameters.packet_size[n_intervalos - 1]
                        }
                    except IndexError:
                        break

                nivel_significativo = 0.05

                for data in components_data:
                    values = components_data[data]
                    if len(values) != 0:
                        avg_value = float(np.mean(values))
                        std_value = float(np.std(values))
                        min_value = float(np.min(values))
                        max_value = float(np.max(values))
                        n = float(len(values))
                        dof = n - 1

                        t_value = t.ppf(1 - nivel_significativo / 2, dof)

                        margin_error = float(t_value * (std_value / np.sqrt(n)))
                        if np.isnan(margin_error):
                            margin_error = 0

                        # Ahora añadir el nuevo valor bajo la clave data
                        data_dict = {
                            "Average": round(avg_value, 2),
                            "Min": round(min_value, 2),
                            "Max": round(max_value, 2),
                            "Sample Size": n,  # El tamaño de la muestra no necesita redondeo
                            "Standard Deviation": round(std_value, 2),
                            "Margin of Error (95% CI)": round(margin_error, 2),
                            "Confidence Interval (95%)": f"{round(avg_value, 2):.2f} +- {round(margin_error, 2):.2f}"
                        }

                    else:
                        data_dict = {
                            "Average": None,
                            "Min": None,
                            "Max": None,
                            "Sample Size": None,
                            "Standard Deviation": None,
                            "Margin of Error (95% CI)": None,
                            "Confidence Interval (95%)": None
                        }

                    element_type = None
                    if data == 'Device':
                        test_statistics[interval_key][data] = data_dict
                    else:
                        if any(sub_string in data for sub_string in ['PIC', 'MPU', 'NPU']):
                            element_type = 'Boards'
                        elif any(sub_string in data for sub_string in ['PSU', 'PowerSupply', 'PS', 'PEM', 'CRXT', 'PM']):
                            element_type = 'PowerSupplies'
                        elif any(sub_string in data for sub_string in ['Transceiver', 'TrRx', 'TRX']):
                            element_type = 'Transceivers'
                        else:
                            element_type = 'Components'
                        if element_type is not None:
                            if element_type not in test_statistics[interval_key]:
                                test_statistics[interval_key][element_type] = {}
                            test_statistics[interval_key][element_type][data] = data_dict

                times_values = []
                for data in components_data:
                    components_data[data] = []

                n_intervalos += 1
                components_data = {component: [] for component in all_components}

        return test_statistics

    def save_in_database(self, test_statistics):
        pass

    def process_test_data_influxdb(self, device_name, test_parameters):
        test_data, all_components = self.time_series_db.influx_filtered_data(device_name, test_parameters)
        logger_cli.info(f"DATOS PROCESS_TEST_DATA_INFLUX: {test_data} y {all_components}")
        test_statistics = self.test_statistics_influxdb(device_name, test_data, test_parameters, all_components)
        self.telemetry_db.save_in_database_influxdb(test_statistics)
        self.static_db.save_data_static(device_name, test_parameters, test_statistics)

class AnalyticsTimeSeriesDB:
    def __init__(self):
        pass

    def query_filtered_data(self, test_parameters):
        logger_cli.info("TODO-influxdb: Create this function")
        pass
    
    def influx_filtered_data(self, device_name, test_parameters):
        logger_cli.info("TODO-influxdb: Create this function")
        test_data = None
        all_components = None
        return test_data, all_components

class AnalyticsTelemetryDB:
    def __init__(self):
        pass

    def save_in_database_influxdb(self, test_statistics):
        logger_cli.info("TODO-influxdb: Create this function")
        pass

class AnalyticsStaticDB:
    def __init__(self):
        pass

    def save_data_static(self, device_name, test_parameters, test_statistics):
        logger_cli.info("TODO-influxdb: Create this function")
        pass