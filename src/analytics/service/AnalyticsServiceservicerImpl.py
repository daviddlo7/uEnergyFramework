import logging
from analytics_pb2 import AnalyticsResponse
from analytics_pb2_grpc import AnalyticsServiceServicer
import math
import numpy as np
from scipy.stats import t
import logging
import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from zoneinfo import ZoneInfo
from datetime import datetime

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
        self.telemetry_db = AnalyticsTelemetryDB()
        self.static_db = AnalyticsStaticDB()
        

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
            'Configuration': test_parameters["configuration"][device_name],
            'Traffic Test': test_parameters["traffic_configuration"],
            'Start Date': test_parameters["start_date"],
            'Start Time': test_parameters["start_time"]
        }

        start_time = None

        if test_parameters["traffic_change"] is None and test_parameters["packet_change"] is None:
            interval = test_parameters["max_interval"] * test_parameters["interval"]
        else:
            if test_parameters["traffic_change"] is None:
                interval = test_parameters["packet_change"]
            elif test_parameters["packet_change"] is None:
                interval = test_parameters["traffic_change"]
            else:
                interval = min(test_parameters["traffic_change"], test_parameters["packet_change"])

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
                if max(times_values) > interval * test_parameters["max_interval"]:
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
                            "Traffic": test_parameters["traffic"] if test_parameters["traffic_change"] is None else
                            test_parameters["traffic"][n_intervalos - 1],
                            "PacketSize": test_parameters["packet_size"] if test_parameters["packet_change"] is None else
                            test_parameters["packet_size"][n_intervalos - 1]
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
        logger_cli.info(f"Pocessing test data influx")
        test_data, all_components = self.time_series_db.influx_filtered_data(device_name, test_parameters)
        logger_cli.info(f"DATOS PROCESS_TEST_DATA_INFLUX: {test_data} y {all_components}")
        test_statistics = self.test_statistics_influxdb(device_name, test_data, test_parameters, all_components)
        logger_cli.info(f"DATOS TEST_STATISTICS: {test_statistics}")
        self.telemetry_db.save_in_database_influxdb(test_statistics)
        self.static_db.save_data_static(device_name, test_parameters, test_statistics)

class AnalyticsTimeSeriesDB:
    def __init__(self):
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.time_series_bucket = "time_series_db_pruebas"

    def query_filtered_data(self, test_parameters):
        logger_cli.info("TODO-influxdb: Create this function")
        pass
    
    def influx_filtered_data(self, device_name, test_parameters):
        results = {}
        all_components = []
        rango = math.ceil(test_parameters["interval"] * test_parameters["max_interval"] / (60 * 60 * 24))
        client = InfluxDBClient(url=self.url_influxdb, token=self.token, org=self.org)
        query_api = client.query_api()

        bucket = self.time_series_bucket
        measurement = device_name
        start_date = test_parameters["start_date"]
        start_time = test_parameters["start_time"]

        columns_to_check = ["board", "component", "transceiver", "power_supply"]
        exists = {}
        for column in columns_to_check:
            query = f'''
                from(bucket: "{bucket}")
                  |> range(start: 0)  
                  |> filter(fn: (r) => r._measurement == "{measurement}") 
                  |> keep(columns: ["{column}"]) 
                  |> group()
                  |> distinct(column: "{column}")
                '''
            result = query_api.query(query=query)
            exists[column] = [record.get_value() for table in result for record in table]

        board_exists = exists["board"]
        component_exists = exists["component"]
        transceiver_exists = exists["transceiver"]
        powersupply_exists = exists["power_supply"]

        power_supply_power = []
        for powersupply in powersupply_exists:
            query = f'''
                    from(bucket: "{bucket}")
                        |> range(start: 0)  
                        |> filter(fn: (r) => r._measurement == "{measurement}") 
                        |> filter(fn: (r) => r["Inst Info"] == "power-supplies")
                        |> filter(fn: (r) => r["power-supply"] == "{powersupply}")
                        |> filter(fn: (r) => r["_field"] == "output_power")
                            '''
            result = query_api.query(query=query)
            if not result:
                power_supply_power.append("input_power")

        parameters = ["DeviceConfiguration", "Scenario", "TestConfiguration", "Times", "traffic_throughput",
                      "traffic_packet_size", "power_device"]

        base_query = f'''
            import "join"
            startDate = from(bucket: "{bucket}")
                      |> range(start: -{rango}d)
                      |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                      |> filter(fn: (r) => r["_field"] == "StartDate")
                      |> filter(fn: (r) => r["_value"] == "{start_date}")
                      //|> rename(columns: {{ "_value": "StartDate" }})
                      |> keep(columns:["_time","_value"])

                    startTime = from(bucket: "{bucket}")
                      |> range(start: -{rango}d)
                      |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                      |> filter(fn: (r) => r["_field"] == "StartTime")
                      |> filter(fn: (r) => r["_value"] == "{start_time}")
                      //|> rename(columns: {{ "_value": "StartTime" }})
                      |> keep(columns:["_time","_value"])
                    t1 = join.time(left: startDate, right: startTime, 
                        method: "inner", 
                        as: (l, r) => ({{l with StartTime: r._value}}))
                            |> rename(columns: {{ "_value": "StartDate" }})
                '''
        cont = 2
        for parameter in parameters:
            base_query = base_query + f'''            
            {parameter} = from(bucket: "{bucket}")
              |> range(start: -{rango}d)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
              |> filter(fn: (r) => r["_field"] == "{parameter}")
              |> keep(columns:["_time","_value"])
            
            t{cont} = join.time(left: t{cont - 1}, right: {parameter}, 
            method: "inner", 
            as: (l, r) => ({{l with {parameter}: r._value}}))
            '''
            cont += 1

        for board in board_exists:
            base_query += f'''
            {board} = from(bucket: "{bucket}")
              |> range(start: -{rango}d)
              |> filter(fn: (r) => r["_measurement"] == "{measurement}")
              |> filter(fn: (r) => r["Inst Info"] == "boards")
              |> filter(fn: (r) => r["board"] == "{board}")
              |> filter(fn: (r) => r["_field"] == "power")
              |> keep(columns:["_time","_value"])
            t{cont} = join.time(left: t{cont - 1}, right: {board}, 
                        method: "left", 
                        as: (l, r) => ({{l with {board}: r._value}}))
            '''
            cont += 1
        for component in component_exists:
            base_query += f'''
                   {component} = from(bucket: "{bucket}")
                     |> range(start: -{rango}d)
                     |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                     |> filter(fn: (r) => r["Inst Info"] == "components")
                     |> filter(fn: (r) => r["component"] == "{component}")
                     |> filter(fn: (r) => r["_field"] == "power")
                     |> keep(columns:["_time","_value"])
                   t{cont} = join.time(left: t{cont - 1}, right: {component}, 
                               method: "left", 
                               as: (l, r) => ({{l with {component}: r._value}}))
                   '''
            cont += 1

        for transceiver in transceiver_exists:
            base_query += f'''
                   {transceiver} = from(bucket: "{bucket}")
                     |> range(start: -{rango}d)
                     |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                     |> filter(fn: (r) => r["Inst Info"] == "transceivers")
                     |> filter(fn: (r) => r["transceiver"] == "{transceiver}")
                     |> filter(fn: (r) => r["_field"] == "power")
                     |> keep(columns:["_time","_value"])
                   t{cont} = join.time(left: t{cont - 1}, right: {transceiver}, 
                               method: "left", 
                               as: (l, r) => ({{l with {transceiver}: r._value}}))
                   '''
            cont += 1

        for i, powersupply in enumerate(powersupply_exists):
            base_query += f'''
                   {powersupply} = from(bucket: "{bucket}")
                     |> range(start: -{rango}d)
                     |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                     |> filter(fn: (r) => r["Inst Info"] == "power-supplies")
                     |> filter(fn: (r) => r["power_supply"] == "{powersupply}")
                     |> filter(fn: (r) => r["_field"] == "{power_supply_power[i]}")
                     |> keep(columns:["_time","_value"])
                   t{cont} = join.time(left: t{cont - 1}, right: {powersupply}, 
                               method: "left", 
                               as: (l, r) => ({{l with {powersupply}: r._value}}))
                   '''
            cont += 1

        final_query = base_query + f'''
                              t{cont - 1} 
                            '''
        try:
            result = query_api.query(query=final_query)
            cont = 0
            if len(result)!=0:
                for table in result:
                    # Recorremos cada registro en la tabla
                    for record in table.records:
                        record.values.pop('result', None)
                        record.values.pop('table', None)
                        dicc = record.values
                        dicc['name'] = device_name
                        results[cont] = dicc
                        cont += 1
        except Exception as e:
            logger_cli.info(f"Error: Processing instantaneous data in InfluxDB: {e}")

        client.close()
        # Devuelve el diccionario
        all_components = all_components + board_exists
        all_components = all_components + transceiver_exists
        all_components = all_components + powersupply_exists
        all_components = all_components + component_exists
        all_components.insert(0, 'Device')

        results_filtered = {}

        for key, data in results.items():
            filtered_data = {}
            for k, v in data.items():
                if v is not None:
                    filtered_data[k] = v
                elif k in all_components:
                    all_components.remove(k)
            results_filtered[key] = filtered_data
        return results_filtered, all_components

class AnalyticsTelemetryDB:
    def __init__(self):
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.telemetry_bucket = "telemetry_db_pruebas"

    def save_in_database_influxdb(self, test_statistics):
        logger_cli.info("Saving in database telemetry influxdb")
        client = InfluxDBClient(url=self.url_influxdb, token=self.token, org=self.org)
        utc_now = datetime.now(ZoneInfo('UTC'))
        current_time = utc_now.astimezone(ZoneInfo('Europe/Berlin'))

        points = []
        for key in test_statistics.keys():
            if key == "Name" or key == "Configuration" or key == "Traffic Test" or key == "Start Date" or key == "Start Time":
                points.append(
                    Point(test_statistics["Name"])
                    .field(key, test_statistics[key])
                    .time(current_time, WritePrecision.NS)
                )
            else:
                dicc = test_statistics[key]
                for tag in dicc.keys():
                    if tag == "StartTime" or tag == "EndTime" or tag == "Time Interval" or tag == "Traffic" or tag == "PacketSize":
                        points.append(
                            Point(test_statistics["Name"])
                            .tag("Intervals", key)
                            .field(tag, dicc[tag])
                            .time(current_time, WritePrecision.NS)
                        )
                    else:
                        if tag == "Device":
                            detail = dicc[tag]
                            for field in detail.keys():
                                points.append(
                                    Point(test_statistics["Name"])
                                    .tag("Intervals", key)
                                    .tag("Power", tag)
                                    .field(field, detail[field])
                                    .time(current_time, WritePrecision.NS)
                                )
                        else:
                            if tag == "Boards":
                                etiqueta = "Board"
                            elif tag == "Components":
                                etiqueta = "Component"
                            elif tag == "Transceivers":
                                etiqueta = "Transceiver"
                            else:
                                etiqueta = "PowerSupply"
                            detail = dicc[tag]
                            for field in detail.keys():
                                dictionary = detail[field]
                                for clave in dictionary.keys():
                                    points.append(
                                        Point(test_statistics["Name"])
                                        .tag("Intervals", key)
                                        .tag("Power", tag)
                                        .tag(etiqueta, field)
                                        .field(clave, dictionary[clave])
                                        .time(current_time, WritePrecision.NS)
                                    )
        write_api = client.write_api(write_options=SYNCHRONOUS)
        try:
            write_api.write(bucket=self.telemetry_bucket, org=self.org, record=points)
        except Exception as e:
            logger_cli.info(f"Error: Saving telemetry data in InfluxDB: {e}")

        client.close()

class AnalyticsStaticDB:
    def __init__(self):
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.static_bucket = "static_db_pruebas"

    def save_data_static(self, device_name, test_parameters, test_statistics):
        logger_cli.info("Saving static data influxdb")
        if os.path.exists("../../../Files/static_device_energy_tid.yang"):
            path = "../../../Files/static_device_energy_tid.yang"
        else:
            path = "Files/static_device_energy_tid.yang"

        static_yang = self.parse_yang_file(path)
        static_yang_device = self.parse_to_yang(device_name, static_yang, test_statistics, test_parameters)
        self.save_static_yang_influxdb(static_yang_device)

    
    def save_static_yang_influxdb(self, dict_yang):
        client = InfluxDBClient(url=self.url_influxdb, token=self.token, org=self.org)
        utc_now = datetime.now(ZoneInfo('UTC'))
        current_time = utc_now.astimezone(ZoneInfo('Europe/Berlin'))

        points = []
        #dict = dict_yang['device']['device']
        for field in dict_yang['device'].keys():
            if field == 'power-supply' or field == 'components' or field == 'boards' or field == 'transceivers':
                for element in dict_yang['device'][field]:
                    for campo in element.keys():
                        if field == 'power-supply':
                            points.append(
                                Point(dict_yang['device']['name'])
                                .tag('power_supply', element['type'])
                                .tag('name', element['name'])
                                .field(campo, element[campo])
                                .time(current_time, WritePrecision.NS)
                            )
                        else:
                            points.append(
                                Point(dict_yang['device']['name'])
                                .tag(field, element['type'])
                                .tag('name', element['name'])
                                .field(campo, element[campo])
                                .time(current_time, WritePrecision.NS)
                            )


            else:
                if field == 'typical-power':
                    points.append(
                        Point(dict_yang['device']['name'])
                        .field('typical-power-device', dict_yang['device'][field])
                        .time(current_time, WritePrecision.NS)
                    )
                elif field == 'nominal-power':
                    points.append(
                        Point(dict_yang['device']['name'])
                        .field('nominal-power-device', dict_yang['device'][field])
                        .time(current_time, WritePrecision.NS)
                    )
                else:
                    points.append(
                        Point(dict_yang['device']['name'])
                        .field(field, dict_yang['device'][field])
                        .time(current_time, WritePrecision.NS)
                    )

        write_api = client.write_api(write_options=SYNCHRONOUS)
        try:
            write_api.write(bucket=self.static_bucket, org=self.org, record=points)
        except Exception as e:
            logger_cli.info(f"Error: Saving static data in InfluxDB: {e}")
        client.close()


    def parse_to_yang(self, device_name, static_yang, test_statistics, test_parameters):
        dicc = test_parameters["devices_static_power_dicc"]
        test_parameters_dict_components = test_parameters["config_data_devices"][device_name]
        efficiency = []
        configuration = test_statistics['Configuration'].split(";")
        configuration_transceivers = [item for item in configuration if
                                      "xT" in item and item[item.index("xT") - 1]]
        number_configuration_transceivers = []
        for value in configuration_transceivers:
            number_configuration_transceivers.append(
                int(value[value.index("xT") - 1]))  #devuelve el numero de los transveivers conectados

        max_power = []
        typical_power = {
            'Device': [],
            'Boards': {},
            'Components': {},
            'Transceivers': {},
            'PowerSupplies': {}
        }
        configuration = [item for item in configuration if item not in configuration_transceivers]
        configuration[:] = [
            item for item in configuration
            if not any(keyword in item for keyword in
                       ['PSU', 'PowerSupply', 'PS', 'PEM', 'CRXT', 'RE', 'CB', 'FPC', 'FanTray', 'SFB', 'TIB','PM'])
        ]

        for item in configuration_transceivers:
            for i, item in enumerate(configuration_transceivers):
                if "xT" in item:
                    idx = item.index("xT") + 2  # El índice después de "xT"
                    configuration_transceivers[i] = item[idx:] #elimina "xxT"

        for key in test_statistics.keys():
            if key != 'Configuration' and key != 'Name' and key != 'Traffic Test' and key != 'Start Date' and key != 'Start Time':
                if test_statistics[key]['EndTime'] - test_statistics[key]['StartTime'] >= 30.0:
                    if test_statistics[key]['PacketSize'] > 0 and test_statistics[key]['Traffic'] > 0:
                        efficiency.append(test_statistics[key]['Device']['Average'] / (
                                    test_statistics[key]['Traffic'] / test_statistics[key]['PacketSize']))
                    for field in test_statistics[key]:
                        if isinstance(test_statistics[key][field], dict):
                            if field == 'Device':
                                if 'Huawei' in device_name:
                                    if 'MPU_11' in configuration and len(configuration)==1 and sum(number_configuration_transceivers) == 0 and \
                                            test_statistics[key]['Traffic'] == 0:  #nada conectado ni trafico
                                        typical_power[field].append(test_statistics[key][field]['Average'])
                                else:
                                    if len(configuration)==0 and sum(number_configuration_transceivers) == 0 and test_statistics[key][
                                        'Traffic'] == 0:
                                        typical_power[field].append(test_statistics[key][field]['Average'])

                                if len(configuration_transceivers) == 1 and "100G" in configuration_transceivers and sum(number_configuration_transceivers) == 2 and test_statistics[key]['Traffic'] == 200 and test_statistics[key][
                                    'PacketSize'] == 62:  # condicion de maximo trafico
                                    max_power.append(test_statistics[key][field]['Average'])

                            else:
                                if 'Huawei' in device_name:
                                    if 'MPU_11' in configuration and len(configuration) == 1 and sum(number_configuration_transceivers) == 0 and \
                                            test_statistics[key]['Traffic'] == 0 and test_statistics[key]['PacketSize'] == 0:  # condicion de maximo trafico:  # nada conectado ni trafico
                                        for element in test_statistics[key][field].keys():
                                            if element not in configuration_transceivers:
                                                typical_power[field].setdefault(element, [])
                                                typical_power[field][element].append(
                                                    test_statistics[key][field][element]['Average'])

                                    else:
                                        break
                                else:
                                    if sum(number_configuration_transceivers) == 0 and test_statistics[key][
                                        'Traffic'] == 0 and test_statistics[key]['PacketSize'] == 0:
                                        for element in test_statistics[key][field].keys():
                                            if element not in configuration_transceivers:
                                                typical_power[field].setdefault(element, [])
                                                typical_power[field][element].append(
                                                    test_statistics[key][field][element]['Average'])

                    if 'Huawei' in device_name:
                        if len(configuration) == 2 and 'MPU_11' in configuration and sum(1 for item in configuration if item.startswith(('NPU'))) == 1 and sum(
                                number_configuration_transceivers) == 0 and test_statistics[key]['Traffic'] == 0 and \
                                test_statistics[key]['PacketSize'] == 0:
                            unique_pic = [item for item in configuration if item.startswith(('NPU'))]
                            typical_power['Boards'].setdefault(unique_pic[0], [])
                            typical_power['Boards'][unique_pic[0]].append(
                                test_statistics[key]['Boards'][unique_pic[0]]['Average'])

                        if len(configuration) == 3 and 'MPU_11' in configuration and sum(
                                1 for item in configuration if item.startswith(('PIC', 'NPU'))) == 2 and \
                                test_statistics[key]['Traffic'] == 0 and test_statistics[key]['PacketSize'] == 0:
                            boards = [item for item in configuration if item.startswith(('PIC', 'NPU'))]
                            if boards[0].startswith('PIC'):
                                if boards[1].startswith('NPU'):
                                    if sum(number_configuration_transceivers) == 1:
                                        typical_power['Transceivers'].setdefault(configuration_transceivers[0], [])
                                        #typical_power['Transceivers'][configuration_transceivers[0]].append(test_statistics[key]['Transceivers'][configuration_transceivers[0]]['Average'])
                                        # sacar el consumo tipico de los transceivers mediante el diccionario de test_parameters.
                                        typical_power['Transceivers'][configuration_transceivers[0]].append(dicc['Huawei']['transceivers'][configuration_transceivers[0]])
                                    if sum(number_configuration_transceivers) == 0:
                                        unique_pic = [item for item in configuration if item.startswith(('PIC'))]
                                        typical_power['Boards'].setdefault(unique_pic[0], [])
                                        typical_power['Boards'][unique_pic[0]].append(test_statistics[key]['Boards'][unique_pic[0]]['Average'])


                            if boards[1].startswith('PIC'):
                                if boards[0].startswith('NPU'):
                                    if sum(number_configuration_transceivers) == 1:
                                        typical_power['Transceivers'].setdefault(configuration_transceivers[0], [])
                                        # typical_power['Transceivers'][configuration_transceivers[0]].append(test_statistics[key]['Transceivers'][configuration_transceivers[0]]['Average'])
                                        # sacar el consumo tipico de los transceivers mediante el diccionario de test_parameters.
                                        typical_power['Transceivers'][configuration_transceivers[0]].append(
                                            dicc['Huawei']['transceivers'][configuration_transceivers[0]])
                                    if sum(number_configuration_transceivers) == 0:
                                        unique_pic = [item for item in configuration if item.startswith(('PIC'))]
                                        typical_power['Boards'].setdefault(unique_pic[0], [])
                                        typical_power['Boards'][unique_pic[0]].append(
                                            test_statistics[key]['Boards'][unique_pic[0]]['Average'])

                    else:
                        if sum(number_configuration_transceivers) == 1 and test_statistics[key][
                            'Traffic'] == 0 and test_statistics[key]['PacketSize'] == 0:
                            typical_power['Transceivers'].setdefault(configuration_transceivers[0], [])
                            if 'Adva' in device_name:
                                nombre = 'Adva'
                            elif 'Ufispace' in device_name:
                                nombre = 'Ufispace'
                            elif 'Juniper' in device_name:
                                nombre = 'Juniper'
                            elif 'Cisco' in device_name:
                                nombre = 'Cisco'
                            typical_power['Transceivers'][configuration_transceivers[0]].append(dicc[nombre]['transceivers'][configuration_transceivers[0]])

        for key in static_yang['device'].keys():
            match key:
                case 'name':
                    static_yang['device'][key] = device_name
                case 'typical-power':
                    if len(typical_power['Device']) > 0:
                        static_yang['device'][key] = float(sum(typical_power['Device'])) / len(typical_power['Device'])
                case 'maximum-traffic-throughput':
                    if 'Ufispace' in device_name:
                        static_yang['device'][key] = dicc['Ufispace']['maximum-traffic-throughput']
                    elif 'Juniper' in device_name:
                        static_yang['device'][key] = dicc['Juniper']['maximum-traffic-throughput']
                    elif 'Adva' in device_name:
                        static_yang['device'][key] = dicc['Adva']['maximum-traffic-throughput']
                    elif 'Huawei' in device_name:
                        static_yang['device'][key] = dicc['Huawei']['maximum-traffic-throughput']

                case 'max-power':
                    if len(max_power) > 0:
                        static_yang['device'][key] = float(sum(max_power)) / len(max_power)
                case 'efficiency':
                    if len(efficiency) > 0:
                        static_yang['device'][key] = float(sum(efficiency)) / len(efficiency)
                case 'nominal-power':
                    if 'Ufispace' in device_name:
                        static_yang['device'][key] = dicc['Ufispace']['nominal-power-device']
                    elif 'Juniper' in device_name:
                        static_yang['device'][key] = dicc['Juniper']['nominal-power-device']
                    elif 'Adva' in device_name:
                        static_yang['device'][key] = dicc['Adva']['nominal-power-device']
                    elif 'Huawei' in device_name:
                        static_yang['device'][key] = dicc['Huawei']['nominal-power-device']

                case 'power-supply':
                    cont = 0
                    for element in typical_power['PowerSupplies'].keys():
                        if element in test_parameters_dict_components.keys():
                            name = test_parameters_dict_components[element]['name']
                            type = test_parameters_dict_components[element]['type']
                            if (not any(d['name'] == name for d in static_yang['device'][key]) or not any(
                                    d['type'] == type for d in static_yang['device'][key])) and cont != 0:
                                static_yang['device'][key].append(copy.deepcopy(static_yang['device'][key][0]))
                                static_yang['device'][key][len(static_yang['device'][key]) - 1]['typical-power'] = []
                            cont = len(static_yang['device'][key]) - 1

                            static_yang['device'][key][cont]['name'] = name
                            static_yang['device'][key][cont]['type'] = type
                            if static_yang['device'][key][cont]['typical-power'] is None:
                                static_yang['device'][key][cont]['typical-power'] = []
                            static_yang['device'][key][cont]['typical-power'] += typical_power['PowerSupplies'][element]

                            if 'Ufispace' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Ufispace']['power-supply'][type][name][
                                    'nominal-power']
                            elif 'Juniper' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Juniper']['power-supply'][type][name][
                                    'nominal-power']
                            elif 'Adva' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Adva']['power-supply'][type][name][
                                    'nominal-power']
                            elif 'Huawei' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Huawei']['power-supply'][type][name][
                                    'nominal-power']
                            cont += 1
                    for i in range(len(static_yang['device'][key])):
                        if static_yang['device'][key][i]['typical-power'] is not None:
                            static_yang['device'][key][i]['typical-power'] = float(sum(static_yang['device'][key][i]['typical-power'])) / len(static_yang['device'][key][i]['typical-power'])

                case 'boards':
                    cont = 0
                    for element in typical_power['Boards'].keys():
                        if element in test_parameters_dict_components.keys():
                            name = test_parameters_dict_components[element]['name']
                            type = test_parameters_dict_components[element]['type']
                            if (not any(d['name'] == name for d in static_yang['device'][key]) or not any(
                                    d['type'] == type for d in static_yang['device'][key])) and cont != 0:
                                static_yang['device'][key].append(copy.deepcopy(static_yang['device'][key][0]))
                                static_yang['device'][key][len(static_yang['device'][key]) - 1]['typical-power'] = []
                            cont = len(static_yang['device'][key]) - 1

                            static_yang['device'][key][cont]['name'] = name
                            static_yang['device'][key][cont]['type'] = type
                            if static_yang['device'][key][cont]['typical-power'] is None:
                                static_yang['device'][key][cont]['typical-power'] = []
                            static_yang['device'][key][cont]['typical-power'] += typical_power['Boards'][element]
                            if 'Ufispace' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Ufispace']['boards'][type][name][
                                    'nominal-power']
                            elif 'Juniper' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Juniper']['boards'][type][name][
                                    'nominal-power']
                            elif 'Adva' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Adva']['boards'][type][name][
                                    'nominal-power']
                            elif 'Huawei' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Huawei']['boards'][type][name][
                                    'nominal-power']
                            cont += 1
                    for i in range(len(static_yang['device'][key])):
                        if static_yang['device'][key][i]['typical-power'] is not None:
                            static_yang['device'][key][i]['typical-power'] = float(
                                sum(static_yang['device'][key][i]['typical-power'])) / len(
                                static_yang['device'][key][i]['typical-power'])

                case 'components':
                    cont = 0
                    for element in typical_power['Components'].keys():
                        if element in test_parameters_dict_components.keys():
                            name = test_parameters_dict_components[element]['name']
                            type = test_parameters_dict_components[element]['type']
                            if (not any(d['name'] == name for d in static_yang['device'][key]) or not any(
                                    d['type'] == type for d in static_yang['device'][key])) and cont != 0:
                                static_yang['device'][key].append(copy.deepcopy(static_yang['device'][key][0]))
                                static_yang['device'][key][len(static_yang['device'][key]) - 1]['typical-power'] = []
                            cont = len(static_yang['device'][key]) - 1

                            static_yang['device'][key][cont]['name'] = name
                            static_yang['device'][key][cont]['type'] = type
                            if static_yang['device'][key][cont]['typical-power'] is None:
                                static_yang['device'][key][cont]['typical-power'] = []
                            static_yang['device'][key][cont]['typical-power'] += typical_power['Components'][element]

                            if 'Ufispace' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Ufispace']['components'][type][
                                    'nominal-power']
                            elif 'Juniper' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Juniper']['components'][type][
                                    'nominal-power']
                            elif 'Adva' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Adva']['components'][type][
                                    'nominal-power']
                            elif 'Huawei' in device_name:
                                static_yang['device'][key][cont]['nominal-power'] = dicc['Huawei']['components'][type][
                                    'nominal-power']
                            cont += 1
                    for i in range(len(static_yang['device'][key])):
                        if static_yang['device'][key][i]['typical-power'] is not None:
                            static_yang['device'][key][i]['typical-power'] = float(
                                sum(static_yang['device'][key][i]['typical-power'])) / len(
                                static_yang['device'][key][i]['typical-power'])

                case 'transceivers': #only one transveicer for typical consumption
                    for element in typical_power['Transceivers'].keys():
                        unique_transceiver = [transceiver for transceiver in test_parameters_dict_components.keys() if transceiver.startswith("TRX")]
                        name = test_parameters_dict_components[unique_transceiver[0]]['name']
                        type = test_parameters_dict_components[unique_transceiver[0]]['type']
                        if type == element:
                            static_yang['device'][key][0]['name'] = name
                            static_yang['device'][key][0]['type'] = type
                            static_yang['device'][key][0]['typical-power'] = float(typical_power['Transceivers'][element][0]['typical-power'])
                            static_yang['device'][key][0]['nominal-power'] = typical_power['Transceivers'][element][0]['nominal-power']

        return static_yang

    def parse_yang_file(self, filename):
            """
                    additional function to read the .yang file and define it in a python dictionary with value None
                    Args:                            
                    filename: the path containing the .yang file

                    Returns: a dictionary with value None

            """
            with open(filename, 'r') as file:
                lines = file.readlines()

            lines_len = len(lines)
            i = 0
            dict = {}
            level_stack = []
            salir = 0
            in_list = 0
            while i < lines_len:
                jumps = 1
                line = lines[i].strip()
                current_dict = dict
                for level in level_stack:
                    current_dict = current_dict[level]
                    if isinstance(current_dict, list):
                        if len(current_dict) == 1:
                            current_dict = current_dict[0]
                            break
                if line.startswith('container'):
                    variable = line.split()[1]
                    if not dict:
                        dict[variable] = {}
                        level_stack.append(variable)
                    else:
                        current_dict[variable] = {}
                        level_stack.append(variable)
                elif line.startswith('leaf'):
                    variable = line.split()[1]
                    current_dict[variable] = None
                    while True:
                        i += 1
                        line = lines[i]
                        if line.strip() == '}':
                            if lines[i + 1].strip() == '}':
                                salir += 1
                            break
                        elif 'type' in line and '{' in line and 'union' not in line:
                            i += 3
                elif line.startswith('list'):
                    variable = line.split()[1]
                    current_dict[variable] = []
                    current_dict[variable].append({})
                    level_stack.append(variable)
                    level_stack.append(0)
                    in_list = 1

                if salir == 1:
                    if in_list == 1:
                        level_stack.pop()
                        in_list = 0
                    level_stack.pop()
                    salir = 0
                i += 1

            return dict