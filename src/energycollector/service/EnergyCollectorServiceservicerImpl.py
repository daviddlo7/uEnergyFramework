import os
import re
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import grpc
import requests
import urllib3
import paramiko
from netmiko import ConnectHandler
from requests.auth import HTTPBasicAuth
import time
from energycollector_pb2 import TestResponse
from energycollector_pb2_grpc import EnergyCollectorServicer
from analytics_pb2 import ProcessTestDataRequest
from analytics_pb2 import CheckConnectionRequest
from analytics_pb2_grpc import AnalyticsServiceStub
from google.protobuf.json_format import MessageToDict
from analytics_pb2 import Device
from analytics_pb2 import PowerData
from analytics_pb2 import Telemetry
from analytics_pb2 import TestParameters
from analytics_pb2 import ConfigDataDevice
from analytics_pb2 import StaticPowerDevice
from analytics_pb2 import StaticPowerComponent
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

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



class EnergyCollectorServicerImpl(EnergyCollectorServicer):
    def __init__(self):
        self.time_series_db = EnergyCollectorTimeSeriesDB()
    
    def RunTest(self, request, context):
        try:
            default_logger.info(f"Received test request for device: {request.test_data}")

            if not request.test_data:
                return TestResponse(message="Error: Test_data not provided.")

            devices = {
                'HL5_1_2_Adva': {
                    'ip': "10.95.90.126",
                    'username': "David.Osa",
                    'password': "9cJk496uLH",
                    'port': "830",
                    'yyy': "adva",
                    'node': '5.5.5.1',
                    'vendor': 'Adva',
                    'info': 'ADVA DRX-30',
                    'interval': 2,
                    'pdu': None
                },
                'HL4_5_1_Huawei': {
                    'ip': "10.95.86.114",
                    'username': "admintid",
                    'password': "Huawei!2015",
                    'port': "830",
                    'yyy': "huaweiyang",
                    'node': '4.4.4.2',
                    'vendor': 'Huawei',
                    'info': 'HUAWEI NE40E-X2-M8A - VRP (R) software, Version 8.221 (NE40E V800R022C10SPC300T)',
                    'interval': 5,
                    'pdu': None
                },
                'HL_Ufispace': {
                    'ip': "10.95.90.75",
                    'username': "dnroot",
                    'password': "dnroot",
                    'port': "830",
                    'yyy': "ufispace",
                    'node': "-",
                    'vendor': "Ufispace",
                    'info': "Ufispace S9700-23D Version: DNOS [18.2.1]build [6]",
                    'interval': 10,
                    'pdu': {'PSU_1': '6;OUTLET38'}
                },
                'HL_Juniper': {
                    'ip': "10.95.90.84",
                    'username': "tid",
                    'password': "jun1per",
                    'port': "830",
                    'yyy': "juniper",
                    'node': "-",
                    'vendor': "Juniper",
                    'info': "Juniper JNMX-304 Junos: 23.4R1.9",
                    'interval': 5,
                    'pdu': {'PEM_1': '6;OUTLET40'}
                },
                'HL_Cisco': {
                    'ip': "10.95.90.150",
                    'username': "cisco",
                    'password': "cisco123",
                    'port': "830",
                    'yyy': "cisco",
                    'node': "-",
                    'vendor': "Cisco",
                    'info': "Cisco NCS-57B1-6D24-SYS",
                    'interval': 5,
                    'pdu':
                        {
                            'PSU_0': '4;OUTLET24',
                            'PSU_1': '4;OUTLET28',
                        }
                }
            }

            devices_list = {
                'HL4_5_1_Huawei': devices['HL4_5_1_Huawei'],
                #'HL5_1_2_Adva': devices['HL5_1_2_Adva'],
                #'HL_Ufispace': devices['HL_Ufispace'],
                #'HL_Juniper': devices['HL_Juniper'],
                #'HL_Cisco': devices['HL_Cisco']
            }

            traffic_configuration = "default"
            escenario = "default"
            total_time = 1
            traffic_change = 0
            traffic = 0
            packet_change = 0
            packet_size = 0
            db = "pruebas"
            db_type = "influxdb"
            web_interface = False
            debug_mode = True
            save_csvs = False
            stop_event = threading.Event()
            influxdb_token = "INFLUXDB_MV_TOKEN_ALL_ACCESS"

            controller = EnergyControllerMain(
                devices_list=devices_list,
                traffic_configuration=traffic_configuration,
                escenario=escenario,
                total_time=total_time,
                traffic_change=traffic_change,
                traffic=traffic,
                packet_change=packet_change,
                packet_size=packet_size,
                db=db,
                db_type=db_type,
                web_interface=web_interface,
                debug_mode=debug_mode,
                save_csvs=save_csvs,
                stop_event=stop_event,
                influxdb_token=influxdb_token
            )

            controller.run()

            logger_cli.info("Waiting for the test to complete...")
            controller.exit_event.wait()  # Esperar hasta que cleanup active el evento

            return TestResponse(message="Test Completed")
            
        except Exception as e:
            default_logger.error(f"An error occurred while running the test: {e}")
            return TestResponse(message="Error")

    def check_analytics_connection(self):
        try:
            channel = grpc.insecure_channel("10.152.183.13:50051")
            stub = AnalyticsServiceStub(channel)

            request = CheckConnectionRequest(id="CheckConnection")
            response = stub.CheckConnection(request)

            channel.close()
            return response.message
        except Exception as e:
            default_logger.error(f"Failed to call CheckConnection on Analytics service: {e}")
            return "Error calling CheckConnection"

            return "Error calling CheckConnection"

    def analytics_process_test_data(self, device_name, test_parameters):
        """
        Calls the Analytics service to process test data.

        :param device_name: Name of the device.
        :param test_parameters: An instance of TestParameters class.
        :return: Response message from the Analytics service.
        """
        try:
            # Create a gRPC insecure channel (no TLS)
            channel = grpc.insecure_channel("10.152.183.13:50051")
            stub = AnalyticsServiceStub(channel)

            # Map devices_list to gRPC Device messages
            devices_list_proto = {
                name: Device(
                    ip=device["ip"],
                    username=device["username"],
                    password=device["password"],
                    port=device["port"],
                    vendor=device["vendor"],
                    info=device["info"]
                )
                for name, device in test_parameters.devices_list.items()
            }

            # Map devices_telemetry to gRPC Telemetry messages
            devices_telemetry_proto = {
                name: Telemetry(times_s=list(telemetry.get("Times_s", [])))
                for name, telemetry in test_parameters.devices_telemetry.items()
            }

            # Map power_data_devices to gRPC PowerData messages
            power_data_devices_proto = {
                name: PowerData(components_power=device)
                for name, device in test_parameters.power_data_devices.items()
            }

            # Map config_data_devices to gRPC ConfigDataDevice messages
            config_data_devices_proto = {
                name: ConfigDataDevice(config_details={
                    key: value["type"]  # Assuming you want to map 'type' as the detail
                    for key, value in device.items()
                })
                for name, device in test_parameters.config_data_devices.items()
            }

            # Map devices_static_power_dicc to gRPC StaticPowerDevice messages
            devices_static_power_dicc_proto = {
                vendor_name: StaticPowerDevice(
                    components_power_data={
                        component_name: StaticPowerComponent(
                            nominal_power_device=component.get("nominal-power", 0),
                            typical_power_device=component.get("typical-power", 0)
                        )
                        for component_name, component in vendor_data.get("transceivers", {}).items()
                    }
                )
                for vendor_name, vendor_data in test_parameters.devices_static_power_dicc.items()
            }

            # Build the TestParameters gRPC message
            test_parameters_proto = TestParameters(
                devices_list=devices_list_proto,
                traffic_configuration=test_parameters.traffic_configuration,
                configuration=test_parameters.configuration,
                escenario=test_parameters.escenario,
                interval=test_parameters.interval,
                max_interval=test_parameters.max_interval,
                traffic_change=test_parameters.traffic_change,
                traffic=test_parameters.traffic,
                actual_traffic=test_parameters.actual_traffic,
                packet_change=test_parameters.packet_change,
                packet_size=test_parameters.packet_size,
                actual_packet_size=test_parameters.actual_packet_size,
                initial_time=float(test_parameters.initial_time),
                initial_datetime=str(test_parameters.initial_datetime),
                start_date=test_parameters.start_date,
                start_time=test_parameters.start_time,
                devices_telemetry=devices_telemetry_proto,
                power_data_devices=power_data_devices_proto,
                web_interface=test_parameters.web_interface,
                config_data_devices=config_data_devices_proto,
                devices_static_power_dicc=devices_static_power_dicc_proto,
                debug_mode=test_parameters.debug_mode,
                influxdb_token=test_parameters.influxdb_token
            )

            # Create the gRPC request
            request = ProcessTestDataRequest(
                device_name=device_name,
                test_parameters=test_parameters_proto
            )

            # Call the remote method
            logger_cli.info("Sending request:")
            logger_cli.info(MessageToDict(request, including_default_value_fields=True))

            response = stub.ProcessTestData(request)

            logger_cli.info(f"Response from Analytics service: {response.message}")

            # Close the channel

            logger_cli.info(f"Response from Analytics service: {response.message}")

            # Close the channel
            channel.close()
            return response.message
        except Exception as e:
            logger_cli.error(f"Error calling ProcessTestData on Analytics service: {e}")
            return "Error calling ProcessTestData"

class EnergyControllerMain:
    def __init__(self, devices_list, traffic_configuration, escenario, total_time, traffic_change,
                 traffic, packet_change, packet_size, db, db_type, web_interface, debug_mode, save_csvs, influxdb_token,
                 stop_event=None, on_finished=None):
        self.reader = None
        self.devices_list = devices_list
        self.traffic_configuration = traffic_configuration
        self.escenario = escenario
        self.total_time = total_time
        self.traffic_change = traffic_change
        self.traffic = traffic
        self.packet_change = packet_change
        self.packet_size = packet_size
        self.db = db
        self.db_type = db_type
        self.web_interface = web_interface
        self.debug_mode = debug_mode
        self.save_csvs = save_csvs
        self.test_parameters = None
        self.stop_event = stop_event
        self.on_finished = on_finished
        self.influxdb_token = influxdb_token
        self.exit_event = threading.Event()
        self.energy_collector_servicer = EnergyCollectorServicerImpl()
        self.time_series_db = EnergyCollectorTimeSeriesDB()
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.bucket = "time_series_db_pruebas"

    def setup(self):
        intervals = [device['interval'] for device in self.devices_list.values()]
        if len(intervals) == 1:
            interval = max(intervals)
        else:
            interval = max(intervals) + 1
            interval = ((max(intervals) + 1 + 4) // 5) * 5
        max_interval = int((self.total_time * 60) / interval)

        time_series_db_name = ''
        static_db_name = ''
        telemetry_db_name = ''
        dashboard_name = ''

        if self.db_type == 'influxdb':
            time_series_db_name = f'time_series_db_{self.db}'
            static_db_name = f'static_db_{self.db}'
            telemetry_db_name = f'telemetry_db_{self.db}'
            dashboard_name = f'dashboard-{self.db_type}-{self.db}'
        elif self.db_type == 'sql':
            time_series_db_name = f'../DataBase/time_series_{self.db}.db'
            static_db_name = f'../DataBase/static_db_{self.db}.db'
            telemetry_db_name = f'../DataBase/telemetry_db_{self.db}.db'
            dashboard_name = f'dashboard-{self.db_type}-{self.db}2'

        self.test_parameters = TestParametersEnergyCollector(
            devices_list=self.devices_list,
            traffic_configuration=self.traffic_configuration,
            escenario=self.escenario,
            interval=interval,
            max_interval=max_interval,
            traffic_change=self.traffic_change,
            traffic=self.traffic,
            actual_traffic=0,
            packet_change=self.packet_change,
            packet_size=self.packet_size,
            actual_packet_size=0,
            power_data_devices={},
            web_interface=self.web_interface,
            debug_mode=self.debug_mode,
            influxdb_token=self.influxdb_token
        )

        logger_cli.info("Devices: " + ", ".join(self.devices_list.keys()))
        logger_cli.info(f'Start Time: {self.test_parameters.start_date}/{self.test_parameters.start_time}')
        logger_cli.info(f'Interval: {interval} seconds')
        logger_cli.info(f'Test Time: {self.total_time} mins.')

        self.reader = Reader()

        # Connection with other pods

        # Calling pod of DB
        # Llamada a influx pidiendole los buckets
        influxdb_result = self.get_influxdb_buckets()
        logger_cli.info(f"Result from Influx pod: {influxdb_result}")
        # Calling pod of Grafana
        # Llamada a Grafana pidiendole los nombres de los dashboards
        grafana_result = self.test_grafana_connection()
        logger_cli.info(f"Result from Grafana pod: {grafana_result}")

        # Calling pod of Analytics
        logger_cli.info("Calling analytics pod")
        analytics_result = self.energy_collector_servicer.check_analytics_connection()
        logger_cli.info(f"Result from analytics pod: {analytics_result}")


        self.test_parameters.devices_telemetry = {}

    def process_device(self, device_name, device_data):
        instantaneous_data_devices = {}
        test_data_devices = {}

        instantaneous_data, test_dict = self.reader.read_data(self.test_parameters, device_name, device_data)

        if not instantaneous_data and not test_dict:
            return

        instantaneous_data_devices[device_name] = instantaneous_data
        test_data_devices[device_name] = test_dict

        power_info = instantaneous_data_devices[device_name].get('device-power-information', {})
        power = power_info.get('power', 'N/A')
        traffic_throughput = power_info.get('performance-metrics', {}).get('traffic-throughput', 'N/A')
        traffic_packet_size = power_info.get('performance-metrics', {}).get('traffic-packet-size', 'N/A')
        times = test_data_devices[device_name].get('Test', {}).get('Times', 'N/A')

        logger_cli.info(f'Name: {device_name}')
        logger_cli.info(f"Times: {times} s ({times / 60:.2f} mins.)")
        logger_cli.info(f'Traffic Throughput (Gbps): {traffic_throughput}')
        logger_cli.info(f'Traffic Packet Size (Bytes): {traffic_packet_size}')
        logger_cli.info(f'Power (W): {power}')

        result = self.time_series_db.save_influxdb_instantaneous_data(device_name, instantaneous_data_devices[device_name],test_data_devices[device_name])

    def event_func(self, interval, max_executions):
        if self.stop_event.is_set():
            logger_cli.info("Stop detected")
            self.cleanup()
            return

        if max_executions > 0:
            max_executions -= 1
            threading.Timer(interval, self.event_func, args=(interval, max_executions)).start()

            threads = []

            logger_cli.info('Reading power data')
            for device_name, device_data in self.devices_list.items():
                thread = threading.Thread(target=self.process_device, args=(
                    device_name, device_data,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            logger_cli.info('Waiting for next iteration to read data')
            

        else:
            time.sleep(5)
            logger_cli.info("Event executions completed.")
            test_statistics_devices = {}
            for device_name, device_data in self.devices_list.items():
                logger_cli.info("Calling Analytics pod to process test data")
                test_statistics = self.energy_collector_servicer.analytics_process_test_data(device_name, self.test_parameters)
                test_statistics_devices[device_name] = test_statistics

                logger_cli.info(f"Result from Analytics pod: {test_statistics}")
                
                # result = self.energy_collector_servicer.save_data_static("device_name", "self.test_parameters", "test_statistics")
                
                if self.save_csvs:
                    logger_cli.info("TODO-csvs: Call DB Pod to save CSV")
                    self.time_series_db.save_csv(self.test_parameters, device_name)

            logger_cli.info("TODO-grafana: Change this URL to the new one of Grafana Pod")
            telemetry_url = f'http://192.168.27.7:3000/d/telemetry-influxdb-{self.db}/telemetry-influxdb-{self.db}?orgId=1&from=946684801&to=946684810'
            logger_cli.info(f'Open telemetry with StartDate {self.test_parameters.start_date} '
                  f'and StartTime {self.test_parameters.start_time} in URL: {telemetry_url}')
            if self.web_interface:
                webbrowser.open(telemetry_url)
            self.cleanup()

    def cleanup(self):
        logger_cli.info("Running cleanup tasks...")
        self.test_parameters.api_session.close()
        if self.on_finished:
            self.on_finished()
        logger_cli.info("TEST ENDED")
        self.exit_event.set()

    def run(self):
        self.setup()
        logger_cli.info('Reading configuration data')
        self.reader.complete_devices_configuration(self.test_parameters)
        logger_cli.info('Configuration data completed. Devices configuration:')
        for device_key, config in self.test_parameters.configuration.items():
            logger_cli.info(f"{device_key}: {config}")
        logger_cli.info('Reading telemetry data')
        self.reader.complete_devices_telemetry(self.test_parameters)
        logger_cli.info('Telemetry data completed')

        utc_now = datetime.now(ZoneInfo('UTC'))
        now = utc_now.astimezone(ZoneInfo('Europe/Berlin'))
        self.test_parameters.initial_time = now.timestamp()
        self.test_parameters.initial_datetime = now

        logger_cli.info("Running power data reader.")
        self.event_func(self.test_parameters.interval, self.test_parameters.max_interval)

    def handle_exit(self, signum=None, frame=None):
        """
        Acción personalizada para manejar Ctrl+C o señales de salida.
        """
        logger_cli.info("Exit detected. Cleaning up before exiting...")
        self.cleanup()
    
    def test_grafana_connection(self):
        grafana_url = "http://10.152.183.15:3000"
        result = {"status_code": None, "response_text": None, "error": None}

        try:
            response = requests.get(grafana_url)
            result["status_code"] = response.status_code
            if response.status_code == 200:
                result["response_text"] = response.text[:200]
            else:
                result["response_text"] = f"Error: HTTP {response.status_code}"
        except Exception as e:
            result["error"] = str(e)

        return result

    def get_influxdb_buckets(self):
        influxdb_url = "http://10.152.183.14:8086/api/v2/buckets"
        headers = {"Authorization": "Token my_admin_token"}
        result = {"status_code": None, "buckets": None, "error": None}

        try:
            response = requests.get(influxdb_url, headers=headers)
            result["status_code"] = response.status_code
            if response.status_code == 200:
                buckets_data = response.json().get("buckets", [])
                bucket_names = ";".join(bucket["name"] for bucket in buckets_data)
                return bucket_names
            else:
                result["buckets"] = f"Error: HTTP {response.status_code}"
        except Exception as e:
            result["error"] = str(e)
            return f"Error: {result['error']}"

class TestParametersEnergyCollector: # TODO Create TestParameters
    """
    Class to store the parameters used during the respective test.

    Attributes:
        telemetry_stats (dict): Test statistics.
    """

    """
        Posibles equipos
        devices = {
            'HL5_1_2_Adva': ["10.95.90.126", "David.Osa", "9cJk496uLH", "830", "adva", '5.5.5.1', 'Adva',
                             'ADVA DRX-30'],
            'HL4_5_1_Huawei': ["10.95.86.114", "admintid", "Huawei!2015", "830", "huaweiyang", '4.4.4.2', 'Huawei',
                               'HUAWEI NE40E-X2-M8A - VRP (R) software, Version 8.221 (NE40E V800R022C10SPC300T)'],
            'HL_Ufispace': ["10.95.90.75", "dnroot", "dnroot", "830", "ufispace", "-", "Ufispace",
                            "Ufispace S9700-23D Version: DNOS [18.2.1]build [6]", '6;OUTLET38'],
            'HL_Juniper': ["10.95.90.84", "tid", "jun1per", "830", "juniper", "-", "Juniper",
                           "Juniper JNMX-304 Junos: 23.4R1.9", '6;OUTLET40'],
            'PDU_Ufispace': ["192.168.27.2", "david", "VirtEned0s", "830", "Ufispace", '38', 'PDU',
                       'Ufispace S9700-23D Version: DNOS '
                       '[18.2.1]build [6]']
        }
        
    """

    def __init__(self, devices_list=None, traffic_configuration=None, configuration=None,
                 escenario=None, interval=None, max_interval=None, traffic_change=None, traffic=None,
                 actual_traffic=None, packet_change=None, packet_size=None, actual_packet_size=None,
                 initial_time=None, initial_datetime=None, devices_telemetry=None, power_data_devices=None,
                 web_interface=True, config_data_devices=None, devices_static_power_dicc=None, debug_mode=False, influxdb_token=None):
        self.devices_list = devices_list
        self.traffic_configuration = traffic_configuration
        self.configuration = {}
        self.escenario = escenario
        self.interval = interval
        self.max_interval = max_interval
        self.traffic_change = traffic_change
        self.traffic = traffic
        self.actual_traffic = actual_traffic
        self.packet_change = packet_change
        self.packet_size = packet_size
        self.actual_packet_size = actual_packet_size
        self.initial_time = initial_time
        self.initial_datetime = initial_datetime
        self.devices_telemetry = devices_telemetry
        self.power_data_devices = power_data_devices
        self.web_interface = web_interface
        self.influxdb_token = influxdb_token

        now = datetime.now()
        self.start_time = now.strftime("%H-%M-%S")
        self.start_date = now.strftime("%d_%m_%Y")

        self.api_session = requests.Session()

        self.config_data_devices = {}

        self.devices_static_power_dicc = {
            'Huawei': {
                'maximum-traffic-throughput': '1Tbps (200Gbps)',
                'nominal-power-device': 550,
                'power-supply': {
                    'PSU': {
                        'PSU Huawei': {
                            'nominal-power': None
                        }
                    }
                },
                'boards': {
                    'PIC': {
                        '2-Port 50GBase/1-Port 100GBase-QSFP28 Physical Interface Card(PIC)': {
                            'nominal-power': None
                        },
                        '10-Port 100/1000Base-X-SFP Physical Interface Card(PIC)':{
                            'nominal-power': None
                        },
                        '4-Port 10GBase LAN/WAN-SFP+ Physical Interface Card(PIC)':{
                            'nominal-power': None
                        }
                    },
                    'NPU': {
                        'NPU-1T': {
                            'nominal-power': None
                        }
                    },
                    'MPU': {
                        'MPU K1': {
                            'nominal-power': None
                        }
                    }
                },
                'transceivers': {
                    '10G': {
                        'nominal-power': None,
                        'typical-power': None
                    },
                    '100G': {
                        'nominal-power': 3.5,
                        'typical-power': 3
                    },
                    '400G': {
                        'nominal-power': 12,
                        'typical-power': 21
                    }
                }
            },
            'Adva': {
                'maximum-traffic-throughput': '300Gbps (200Gbps)',
                'nominal-power-device': None,
                'power-supply': {
                    'CRXT': {
                        'CRXT_T0T12A': {
                            'nominal-power': None
                        }
                    }
                },
                'transceivers': {
                    '10G': {
                        'nominal-power': None,
                        'typical-power': None
                    },
                    '100G': {
                        'nominal-power': 3.5,
                        'typical-power': 3
                    },
                    '400G': {
                        'nominal-power': 12,
                        'typical-power': 21
                    }
                }
            },
            'Juniper': {
                'maximum-traffic-throughput': '4.8Tbps (200Gbps)',
                'nominal-power-device': None,
                'power-supply': {
                    'PEM': {
                        'AC AFO 2200W Power Supply': {
                            'nominal-power': None
                        }
                    }

                },
                'components': {
                    'RE': {
                        'nominal-power': None
                    },
                    'CB': {
                        'nominal-power': None
                    },
                    'FPC': {
                        'nominal-power': None
                    },
                    'Fan Tray': {
                        'nominal-power': None
                    },
                    'SFB': {
                        'nominal-power': None
                    },
                    'TIB': {
                        'nominal-power': None
                    }
                },
                'transceivers': {
                    '10G': {
                        'nominal-power': None,
                        'typical-power': None
                    },
                    '100G': {
                        'nominal-power': 3.5,
                        'typical-power': 3
                    },
                    '400G': {
                        'nominal-power': 12,
                        'typical-power': 21
                    }
                }
            },
            'Ufispace': {
                'maximum-traffic-throughput': '4.8Tbps (200Gbps)',
                'nominal-power-device': None,
                'power-supply': {
                    'PSU': {
                        'AM-2A02P10': {
                            'nominal-power': None
                        }
                    }
                },
                'transceivers': {
                    '10G': {
                        'nominal-power': None,
                        'typical-power': None
                    },
                    '100G': {
                        'nominal-power': 3.5,
                        'typical-power': 3
                    },
                    '400G': {
                        'nominal-power': 12,
                        'typical-power': 21
                    }
                }
            },
            'Cisco': {
                'maximum-traffic-throughput': '',
                'nominal-power-device': None,
                'power-supply': {
                    'PSU': {
                        'PM': {
                            'nominal-power': None
                        }
                    }
                },
                'transceivers': {
                    '10G': {
                        'nominal-power': None,
                        'typical-power': None
                    },
                    '100G': {
                        'nominal-power': 3.5,
                        'typical-power': 3
                    },
                    '400G': {
                        'nominal-power': 12,
                        'typical-power': 21
                    }
                }
            }
        }

        self.debug_mode = debug_mode

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

    def __str__(self):
        # Include all attributes in the string representation
        return f"Test Parameters: {self.__dict__}"

    def __repr__(self):
        # Include all attributes in the representation with better formatting
        attrs = ',\n  '.join(f"{key}={value!r}" for key, value in self.__dict__.items())
        return f"TestParameters(\n  {attrs}\n)"

    def to_dict(self):
        return self.__dict__

class Reader:
    """
    Class in charge of reading the energy consumption data of all equipment and displaying it in the given YANG format.

    Attributes:
    """

    def __init__(self):
        pass

    def read_data(self, test_parameters, device_name, device_data):
        """
        Function that collects data from devices
        Args:
            test_parameters: test parameters to be used
        """
        # Consult the energy consumption of the device, either via PDU or CLI
        if test_parameters.debug_mode:
            logger_cli.info(f'Reading data for {device_name}')
        else:
            logger_cli.info('...')
        utc_now = datetime.now(ZoneInfo('UTC'))
        now = utc_now.astimezone(ZoneInfo('Europe/Berlin'))
        instantaneous_data_yang = {}

        try:
            power_info_cli, power_info_pdu = self.get_power_consumption(device_data, device_name,
                                                                        test_parameters.api_session,
                                                                        test_parameters)
            instantaneous_data_yang = self.parse_to_yang(device_name, power_info_cli,
                                                         power_info_pdu)  # Parse to dynamic YANG Model

        except Exception as e:
            logger_cli.info("Error reading power data -> Continue")
            logger_cli.info(e)

        power_info = instantaneous_data_yang.get('device-power-information', {})
        if not power_info or power_info.get('power') is None:
            return {}, {}

        actual_time = float("{:.1f}".format(time.time() - test_parameters.initial_time))
        throughput = 0
        packet_size = 0
        if test_parameters.traffic_change != 0:
            if actual_time < (test_parameters.traffic_change * (test_parameters.actual_traffic + 1)):
                throughput = test_parameters.traffic[test_parameters.actual_traffic]
            else:
                if test_parameters.actual_traffic < len(test_parameters.traffic) - 1:
                    test_parameters.actual_traffic += 1
                    throughput = test_parameters.traffic[test_parameters.actual_traffic]
        else:
            throughput = test_parameters.traffic

        if test_parameters.packet_change != 0:
            if actual_time < (test_parameters.packet_change * (test_parameters.actual_packet_size + 1)):
                packet_size = test_parameters.packet_size[test_parameters.actual_packet_size]
            else:
                if test_parameters.actual_packet_size < len(test_parameters.packet_size) - 1:
                    test_parameters.actual_packet_size += 1
                packet_size = test_parameters.packet_size[test_parameters.actual_packet_size]
        else:
            packet_size = test_parameters.packet_size

        performance_metrics = instantaneous_data_yang['device-power-information'][
            'performance-metrics']
        performance_metrics['traffic-type'] = None
        performance_metrics['traffic-throughput'] = float(throughput)
        performance_metrics['traffic-packet-size'] = int(packet_size)

        if throughput != 0 and packet_size != 0:
            fps = (float(throughput) * float(10 ^ 9)) / (float(packet_size) * 8)
            power = float(instantaneous_data_yang['device-power-information']['power'])
            eff = power / fps
            instantaneous_data_yang['device-power-information']['energy-efficiency'] = eff

        test_dict = {
            'Test': {
                'DeviceConfiguration': test_parameters.configuration[device_name],
                'TestConfiguration': test_parameters.traffic_configuration,
                'Scenario': test_parameters.escenario,
                'StartTime': test_parameters.start_time,
                'StartDate': test_parameters.start_date,
                'DateTime': now,
                'Times': actual_time
            }
        }

        for key in test_parameters.devices_telemetry[device_name].keys():
            match key:
                case 'DateTime':
                    test_parameters.devices_telemetry[device_name][key].append(
                        test_dict['Test']['DateTime'].strftime("%Y-%m-%d %H:%M:%S"))
                case 'Times_s':
                    test_parameters.devices_telemetry[device_name][key].append(test_dict['Test']['Times'])
                case 'Throughput_Gbps':
                    test_parameters.devices_telemetry[device_name][key].append(
                        instantaneous_data_yang['device-power-information']['performance-metrics'][
                            'traffic-throughput'])
                case 'PacketSize_B':
                    test_parameters.devices_telemetry[device_name][key].append(
                        instantaneous_data_yang['device-power-information']['performance-metrics'][
                            'traffic-packet-size'])
                case _:
                    if any(substring in key for substring in ['PIC', 'NPU', 'MPU']):
                        slot = ''
                        for index, dictionary in enumerate(
                                instantaneous_data_yang['device-power-information']['boards']):
                            if dictionary['name'] == key:
                                slot = index
                                test_parameters.devices_telemetry[device_name][key].append(
                                    instantaneous_data_yang['device-power-information']['boards'][slot]['power'])
                                break
                    else:
                        test_parameters.devices_telemetry[device_name][key].append(
                            instantaneous_data_yang['device-power-information']['power'])

        return instantaneous_data_yang, test_dict

    def complete_devices_telemetry(self, test_parameters):
        """
        This function performs a first reading of the data in the equipment to know what format it will have, as it
        depends on each one, and even if it is CLI or PDU.
        Args:
            test_parameters: test parameters to be used
        """
        for device_name, device_data in test_parameters.devices_list.items():

            test_parameters.devices_telemetry[device_name] = {'DateTime': deque(maxlen=test_parameters.max_interval),
                                                              'Times_s': deque(maxlen=test_parameters.max_interval),
                                                              'Throughput_Gbps': deque(
                                                                  maxlen=test_parameters.max_interval),
                                                              'PacketSize_B': deque(
                                                                  maxlen=test_parameters.max_interval)}

            # Consult energy consumption
            if test_parameters.debug_mode:
                logger_cli.info(f'Reading telemetry data for: {device_name}')
            else:
                logger_cli.info('...')
            power_info_device = self.cli_power_data(device_data, device_name, test_parameters)
            if 'huawei' in device_name.lower():
                for key, value in power_info_device['chassis-boards'].items():
                    test_parameters.devices_telemetry[device_name][value['Type'] + '_' + value['Slot']] = deque(
                        maxlen=test_parameters.max_interval)
            elif 'adva' in device_name.lower():
                for key, value in power_info_device['power-supply'].items():
                    if value['Oper'] == 'Ok':
                        test_parameters.devices_telemetry[device_name][value['Inserted']] = deque(
                            maxlen=test_parameters.max_interval)
            elif 'juniper' in device_name.lower():
                for key, value in power_info_device['chassis-components'].items():
                    if key.find('System') != -1:
                        test_parameters.devices_telemetry[device_name][key + " (W)"] = deque(
                            maxlen=test_parameters.max_interval)
                    if key.find('Items') != -1:
                        for valor in value:
                            test_parameters.devices_telemetry[device_name][valor] = deque(
                                maxlen=test_parameters.max_interval)
            elif 'ufispace' in device_name.lower():
                test_parameters.devices_telemetry[device_name]['NodePower'] = deque(maxlen=test_parameters.max_interval)
            elif 'cisco' in device_name.lower():
                test_parameters.devices_telemetry[device_name]['Total Power(W)'] = deque(
                    maxlen=test_parameters.max_interval)

    def api_power_data(self, device, device_name, session, ps_outlet):
        """
        Function that makes the API call to the corresponding power strip and outlet.
        Args:
            rack_outlet:
            device: device parameters
            device_name: name of the device to be consulted
            session: HTTP session with the PDU via API

        Returns: dictionary with all obtained energy consumption data

        """
        hostname = device['ip']
        username = device['username']
        password = device['password']
        vendor = device['vendor']
        info = device['info']
        rack = ps_outlet.split(';')[0]
        outlet = ps_outlet.split(';')[1]
        url = f"http://192.168.27.2/redfish/v1/PowerEquipment/RackPDUs/{rack}/Outlets/{outlet}"
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        username = "david"
        password = "Virtened0s"

        power_data_equipo = {}
        try:
            response = session.get(url, auth=HTTPBasicAuth(username, password), verify=False)

            if response.status_code == 200:
                power_data_equipo = response.json()
            else:
                logger_cli.info(f'Failed to retrieve data: {response.status_code}')
                logger_cli.info(response.text)
        except requests.exceptions.RequestException as e:
            logger_cli.info(f'Request failed: {e}')
            power_data_equipo = {'Error:': e}

        return power_data_equipo

    def cli_power_data(self, device, device_name, test_parameters):
        """
        Function that makes the CLI call to the device.
        Args:
            device: device parameters
            device_name: name of the device to be consulted

        Returns: dictionary with all obtained energy consumption data

        """
        hostname = device['ip']
        username = device['username']
        password = device['password']
        vendor = device['vendor']
        info = device['info']
        name = info.split(' ')[0] + ' ' + info.split(' ')[1]
        power_data = {
            'Name': device_name
        }
        power_data_device = {}
        if vendor.lower() == 'huawei':
            commands = {}
            if info.find("NE40E") != -1:
                if info.find("NE40E V800R022C10") != -1:
                    commands = {
                        'chassis-boards': ['display power consumption'],
                        'power-supply': ['display power environment-info slot 13',
                                         'display power environment-info slot 14'],
                        #'cpu': ['display cpu-usage'],
                        #'fan': ['display fan'],
                        #'energy-mode': ['display energy-mode mode']

                    }
                else:
                    commands = {
                        'chassis-boards': 'display board-power'
                    }
            elif info.find("ATN") != -1:
                if info.find("ATN 950C V800R022C10") != -1:
                    commands = {
                        'chassis-boards': 'display power consumption'
                    }
                else:
                    commands = {
                        'chassis-boards': 'display power slot detail'
                    }

            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'adva':
            commands = {
                'power-supply': ['show power-supply table'],
                'cpu': ['show cpu usage'],
                'fan': ['show fan slot 1 speed']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    command = f'vtysh -e "{command}" '
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'nokia':
            logger_cli.info("Nokia device can't get power information")
            command = 'show version'
            device = {
                'device_type': 'nokia_sros',
                'ip': hostname,
                'username': username,
                'password': password,
                'port': 22,
                'verbose': False
            }
            with ConnectHandler(**device) as net_connect:
                if test_parameters.debug_mode:
                    logger_cli.info(f"Executing command: {command}")
                cli_text = net_connect.send_command(command)
            logger_cli.info("Nokia device can't get power information")
        elif vendor.lower() == 'cisco':
            commands = {
                'power-supply': ['show environment power'],
                'fan': ['show environment fan']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'ufispace':
            commands = {
                'all': ['show system hardware power detail;show system hardware']
            }

            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'juniper':
            commands = {
                'chassis-components': ['show chassis power detail'],
                'fan': ['show chassis fan'],
                'power-supply': ['show chassis environment pem']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    time.sleep(1)
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()

        return power_data_device

    def execute_command_in_thread(self, command, hostname, username, password, test_parameters, power_data_device,
                                  metric, device_name, info):
        try:
            if 'ufispace' in device_name.lower():
                device = {
                    'device_type': 'nokia_sros',
                    'ip': hostname,
                    'username': username,
                    'password': password,
                    'port': 22,
                    'verbose': False
                }
                with ConnectHandler(**device) as net_connect:
                    if test_parameters.debug_mode:
                        logger_cli.info(f"Executing command: {command}")
                    cli_text = net_connect.send_command(command)
                    power_data_equipo = self.parse_cli(cli_text, device_name, info, metric)
                    power_data_device.update(power_data_equipo)

            else:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                try:
                    ssh_client.connect(hostname=hostname, username=username, password=password)
                except Exception as e:
                    logger_cli.info(f"[!] Cannot connect to the SSH Server: {e}")
                    return

                if command != 'screen-length 0 temporary':
                    if test_parameters.debug_mode:
                        logger_cli.info(f"Executing command: {command}")
                    cli_text = self.execute_command(command, ssh_client)

                    if metric == 'boards-slot':
                        boards = self.parse_cli(cli_text, device_name, info, metric)
                        metric = 'boards'

                        threads = []
                        for board_slot in boards:
                            time.sleep(1)
                            thread = threading.Thread(target=self.process_board_slot,
                                                      args=(board_slot, hostname, username, password, test_parameters,
                                                            power_data_device, metric, device_name, info))
                            threads.append(thread)
                            thread.start()

                        for thread in threads:
                            thread.join()

                    else:
                        power_data_equipo = self.parse_cli(cli_text, device_name, info, metric)
                        with threading.Lock():
                            if 'config' in metric:
                                power_data_device.update(power_data_equipo)
                            else:
                                power_data_device.setdefault(metric, {}).update(power_data_equipo)

                ssh_client.close()
        except Exception as e:
            logger_cli.info(f"[!] Error in CLI, executing command: {e}")
            raise

    def process_board_slot(self, board_slot, hostname, username, password, test_parameters, power_data_device,
                           metric, device_name, info):
        try:
            # Crear una nueva conexión SSH para cada board_slot
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Intentar conectar al servidor SSH para el board_slot
            try:
                ssh_client.connect(hostname=hostname, username=username, password=password)
            except Exception as e:
                logger_cli.info(f"[!] Cannot connect to the SSH Server for board slot {board_slot}: {e}")
                time.sleep(1)
                return

            # Comando específico para cada board_slot
            command = f'display boardinfo slot {board_slot} eeprom 0'
            if test_parameters.debug_mode:
                logger_cli.info(f"Executing command: {command}")
            cli_text = self.execute_command(command, ssh_client)

            # Procesar los datos de la board
            board = self.parse_cli(cli_text, device_name, info, metric)
            board_name = board['type'] + '_' + str(board_slot)

            # Usar Lock para actualizar power_data_device de manera segura
            with threading.Lock():
                power_data_device.setdefault(board_name, {}).update(board)

            # Cerrar la sesión SSH después de ejecutar el comando para este board_slot
            ssh_client.close()

        except Exception as e:
            if test_parameters.debug_mode:
                logger_cli.info(f"[!] Error processing board slot {board_slot}: {e}")

            # Verificar si el error es el TypeError("'int' object is not subscriptable")
            if isinstance(e, TypeError) and str(e) == "'int' object is not subscriptable":
                if test_parameters.debug_mode:
                    logger_cli.info(f"[!] Retrying board slot {board_slot} due to TypeError: {e}")

                # Cerrar la sesión SSH si existe antes de reintentar
                try:
                    ssh_client.close()
                except:
                    pass

                # Reintentar el procesamiento de board_slot
                self.process_board_slot(board_slot, hostname, username, password, test_parameters, power_data_device,
                                        metric, device_name, info)

    def execute_command(self, command, ssh_client):
        """
        function that simply makes a CLI call and executes the corresponding command
        Args:
            command:
            ssh_client: ssh session being used

        Returns: command output in text format

        """
        stdin, stdout, stderr = ssh_client.exec_command(command)
        file = stdout.read().decode()
        err = stderr.read().decode()
        if err:
            logger_cli.info(err)
            return err
        else:
            return file

    def extractDataBetweenLines(self, cli_text, start_lines, end_lines):
        """
        additional function to remove uninteresting data from the command output, removing lines at both the beginning
        and the end of the command output
        Args:
            cli_text: text returned by the command
            start_lines: lines to be removed at the start of the text
            end_lines: lines to be removed at the end of the text

        Returns: new text without removed lines

        """
        lines = cli_text.split('\n')

        total_lines = len(lines)

        cli_text = lines[start_lines:(total_lines - end_lines)]

        # Join the remaining lines to reconstruct the text
        result_text = '\n'.join(cli_text)

        return result_text

    def get_power_consumption(self, device_data, device_name, api_session, test_parameters):

        power_info_cli, power_info_pdu = self.obtain_power_data(device_data, device_name, api_session,
                                                                test_parameters)

        return power_info_cli, power_info_pdu

    def parse_to_yang(self, device_name, power_data_cli, power_info_pdu):
        if os.path.exists('/app/Files/instantaneous_device_energy_tid.yang'):
            path = '/app/Files/instantaneous_device_energy_tid.yang'
        else:
            path = '/app/Files/instantaneous_device_energy_tid.yang'
        dict_yang = self.parse_yang_file(path)

        device_inst_dict = self.cli_to_yang(device_name, power_data_cli, dict_yang)
        if power_info_pdu:
            self.pdu_to_yang(device_name, device_inst_dict, power_info_pdu)
        return device_inst_dict

    def cli_to_yang(self, device_name, power_data, dict_yang):
        for key, value in power_data.items():
            pass
            if key == 'name':
                dict_yang['device-power-information']['name'] = value
            elif key == 'chassis-boards':
                board_list = []
                for key2, values2 in value.items():
                    if key2 == 'Chassis_.':
                        dict_yang['device-power-information']['power'] = round(
                            float(value['Chassis_.']['CurrentPower(W)']), 2)
                    else:
                        board_dict = {
                            'name': values2['Type'] + "_" + values2['Slot'],
                            'type': values2['Type'],
                            'power': round(float(values2['CurrentPower(W)']), 2),
                        }
                        board_list.append(board_dict)
                dict_yang['device-power-information']['boards'] = board_list
            elif key == 'power-supply':
                psu_list = []
                psu_dict = {}
                for key2, values2 in value.items():
                    if 'huawei' in device_name.lower():
                        psu_dict = {
                            'name': key2,
                            'rated-power': None,
                            'input-current': round(float(values2['Power[0] current']), 2),
                            'input-voltage': round(float(values2['Power[0] voltage']), 2),
                            'input-power': round(
                                float(values2['Power[0] current']) * float(values2['Power[0] voltage']),
                                2),
                            'output-current': None,
                            'output-voltage': None,
                            'output-power': None,
                            'efficiency': None
                        }
                        psu_list.append(psu_dict)
                    elif 'adva' in device_name.lower():
                        if values2['Oper'] == 'Ok':
                            psu_dict = {
                                'name': key2,
                                'rated-power': None,
                                'input-current': round(float(values2['InI']), 2),
                                'input-voltage': round(float(values2['InV']), 2),
                                'input-power': round(float(values2['InP']), 2),
                                'output-current': round(float(values2['OutI']), 2),
                                'output-voltage': round(float(values2['OutV']), 2),
                                'output-power': round(float(values2['OutP']), 2),
                                'efficiency': round(float(values2['OutP']) / float(values2['InP']), 2)
                            }
                            dict_yang['device-power-information']['power'] = round(float(values2['InP']), 2)
                            psu_list.append(psu_dict)
                    elif 'juniper' in device_name.lower():
                        if values2['State'] == 'Online':
                            psu_dict = {
                                'name': key2,
                                'rated-power': None,
                                'input-current': round(float(values2['Input']['Current(A)']), 2),
                                'input-voltage': round(float(values2['Input']['Voltage(V)']), 2),
                                'input-power': round(float(values2['Input']['Power(W)']), 2),
                                'output-current': round(float(values2['Output']['Current(A)']), 2),
                                'output-voltage': round(float(values2['Output']['Voltage(V)']), 2),
                                'output-power': round(float(values2['Output']['Power(W)']), 2),
                                'efficiency': round(
                                    float(values2['Output']['Power(W)']) / float(values2['Input']['Power(W)']), 2)
                            }
                            psu_list.append(psu_dict)
                    elif 'ufispace' in device_name.lower():
                        if values2['status'] == 'OK':
                            psu_dict = {
                                'name': key2,
                                'rated-power': None,
                                'input-current': None,
                                'input-voltage': None,
                                'input-power': values2['input-power'],
                                'output-current': None,
                                'output-voltage': None,
                                'output-power': None,
                                'efficiency': None
                            }
                            psu_list.append(psu_dict)
                    elif 'cisco' in device_name.lower():
                        if key2 == 'Total Input Power':
                            dict_yang['device-power-information']['power'] = values2
                        elif 'PM' in key2:
                            psu_dict = {
                                'name': key2,
                                'rated-power': None,
                                'input-current': float(values2['Amps Input']),
                                'input-voltage': float(values2['Volts Input']),
                                'input-power': round(float(values2['Amps Input']) * float(values2['Volts Input']), 2),
                                'output-current': float(values2['Amps Output']),
                                'output-voltage': float(values2['Volts Output']),
                                'output-power': float(values2['Amps Output']) * float(values2['Volts Output']),
                                'efficiency': round((float(values2['Amps Output']) * float(values2['Volts Output'])) / (
                                        float(values2['Amps Input']) * float(values2['Volts Input'])), 2)
                            }
                            psu_list.append(psu_dict)
                dict_yang['device-power-information']['power-supply'] = psu_list
            elif key == 'fan':
                if 'huawei' in device_name.lower():
                    dict_yang['device-power-information']['performance-metrics']['fan-speed'] = int(
                        value['FAN']['Usage(%)'])
                elif 'adva' in device_name.lower():
                    dict_yang['device-power-information']['performance-metrics']['fan-speed'] = float(
                        value['FAN']['Usage(RPM)'])
                elif 'juniper' in device_name.lower():
                    percent_rpm = [float(item['%RPM'].strip('%')) for item in value.values()]
                    rpm = [item['RPM'] for item in value.values()]

                    mean_percent_rpm = float(sum(percent_rpm) / len(percent_rpm))
                    mean_rpm = float(sum(rpm) / len(rpm))
                    dict_yang['device-power-information']['performance-metrics']['fan-speed'] = mean_rpm
                elif 'ufispace' in device_name.lower():
                    dict_yang['device-power-information']['performance-metrics']['fan-speed'] = float(
                        value['FAN']['Usage(RPM)'])
                elif 'cisco' in device_name.lower():
                    dict_yang['device-power-information']['performance-metrics']['fan-speed'] = float(
                        sum(value.values()) / len(value.values()))
            elif key == 'energy-mode':
                dict_yang['device-power-information']['energy-mode'] = value['Mode']
            elif key == 'cpu':
                dict_yang['device-power-information']['performance-metrics']['cpu-load'] = int(value['CPU']['Usage(%)'])
            elif key == 'chassis-components':
                for key2, value2 in value.items():
                    if key2 == 'System':
                        dict_yang['device-power-information']['power'] = value2['Actual usage'].split()[0]
                    elif key2 == 'Items':
                        component_list = []
                        for component_name, component_value in value2.items():
                            component_name = component_name.split()[0]
                            component_type = ''
                            if 'fan' in component_name.lower():
                                component_type = 'Fan'
                            elif any(keyword in component_name.lower() for keyword in ['sfb', 'fpc', 're']):
                                component_type = 'Module'
                            component = {
                                'name': component_name,
                                'type': component_type,
                                'power': component_value,
                            }
                            component_list.append(component)
                        dict_yang['device-power-information']['components'] = component_list
            elif key == 'node':
                dict_yang['device-power-information']['power'] = value['power']
            elif key == 'temperature':
                dict_yang['device-power-information']['performance-metrics']['ambient-temperature'] = int(
                    value['Ambient(ºC)'])

        return dict_yang

    def parse_yang_file(self, filename):
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

    def parse_cli(self, cli_text, device_name, info, type):
        power_data_equipo = {}
        config_data_equipo = {}
        board_slots = []
        name = ''
        type2 = ''
        if 'huawei' in device_name.lower():
            if 'chassis-boards' in type:
                if info.find("NE40E-X8") != -1:
                    if info.find("NE40E V800R022C10") != -1:
                        chassis_power = ".         Chassis  "
                        space = "        "
                        for line in cli_text.splitlines()[7:12]:
                            line = line.replace(" ", "")
                            variable, value = line.split(":")
                            try:
                                chassis_power = chassis_power + "{:.2f}".format(float(value)) + space
                            except:
                                continue
                            space = space + "    "

                        board_power = self.extractDataBetweenLines(cli_text, 14, 5)
                        cli_text = board_power.splitlines()[:1] + [chassis_power] + board_power.splitlines()[1:]
                        cli_text = os.linesep.join([line for line in cli_text if line])
                    else:
                        cli_text = self.extractDataBetweenLines(cli_text, 6, 5)
                        cli_text = cli_text.replace(
                            '------------------------------------------------------------------', '')
                        cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])
                elif info.find("ATN") != -1:
                    if info.find("ATN 950C V800R022C10") != -1:
                        chassis_power = ".         Chassis  "
                        space = "        "
                        for line in cli_text.splitlines()[9:13]:
                            line = line.replace(" ", "")
                            variable, value = line.split(":")
                            try:
                                chassis_power = chassis_power + "{:.2f}".format(float(value)) + space
                            except:
                                continue
                            space = space + "    "

                        board_power = self.extractDataBetweenLines(cli_text, 15, 5)
                        cli_text = board_power.splitlines()[:1] + [chassis_power] + board_power.splitlines()[1:]
                        cli_text = os.linesep.join([line for line in cli_text if line])
                    else:
                        cli_text = self.extractDataBetweenLines(cli_text, 5, 5)
                        cli_text = cli_text.replace(
                            '--------------------------------------------------------------------', '')
                        cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])
                elif info.find("NE40E-X2") != 1:
                    if info.find("NE40E V800R022C10") != -1:
                        chassis_power = ".         Chassis  "
                        space = "        "
                        for line in cli_text.splitlines()[6:11]:
                            line = line.replace(" ", "")
                            variable, value = line.split(":")
                            try:
                                chassis_power = chassis_power + "{:.2f}".format(float(value)) + space
                            except:
                                continue
                            space = space + "    "

                        board_power = self.extractDataBetweenLines(cli_text, 12, 5)
                        cli_text = board_power.splitlines()[:1] + [chassis_power] + board_power.splitlines()[1:]
                        cli_text = os.linesep.join([line for line in cli_text if line])
                    else:
                        indexes = []
                        parse_text = ""
                        lines = cli_text.split('\n')
                        for number, line in enumerate(cli_text.splitlines()):
                            if 'Slot' in line:
                                indexes.append(number)
                        for n, index in enumerate(indexes):

                            if n == 0:
                                cli_text = parse_text + lines[index + 1]

                            cli_text = cli_text + '\n' + lines[index + 3]

                        cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])

                count = 0
                variables = {}

                for line in cli_text.splitlines():
                    if count == 0:
                        variables = line.split()
                    else:
                        valores = line.split()
                        values = dict(zip(variables, valores))
                        power_data_equipo[values['Type'] + '_' + values['Slot']] = values
                    count += 1
            elif 'power-supply' in type:
                cli_text = self.extractDataBetweenLines(cli_text, 5, 5)
                cli_text = cli_text.replace(
                    '------------------------------------------------------------------', '')
                cli_text = cli_text.replace(
                    '-----------------------------------', '')
                cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])

                count = 0
                total_psu = {}
                psu = ''

                for line in cli_text.splitlines():
                    if count == 0:
                        line = line[1:]
                        line_words = line.split()
                        psu = f"PSU_{line_words[1]}"
                        power_data_equipo[psu] = {}

                    else:
                        left, right = line.split(":")
                        variable = left.strip()
                        value = right.strip()
                        total_psu[variable] = value
                    count += 1
                power_data_equipo[psu] = total_psu
            elif 'cpu' in type:
                cli_text = self.extractDataBetweenLines(cli_text, 6, 5)
                cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])

                count = 0
                total_psu = {}

                for line in cli_text.splitlines():
                    if count == 0:
                        cpu_rate = line.split(':')[1].strip().rstrip('%')
                        power_data_equipo.setdefault('CPU', {}).setdefault('Usage(%)', cpu_rate)
                        break
            elif 'fan' in type:
                cli_text = self.extractDataBetweenLines(cli_text, 10, 4)
                cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])

                fan_utilization = []
                average_utilization = 0

                for line in cli_text.splitlines():
                    matches = re.findall(r'(\d+)%', line)
                    fan_utilization.extend([int(match) for match in matches])

                average_utilization = sum(fan_utilization) / len(fan_utilization)

                power_data_equipo.setdefault('FAN', {}).setdefault('Usage(%)', average_utilization)
            elif 'energy-mode' in type:
                cli_text = self.extractDataBetweenLines(cli_text, 5, 4)
                cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])

                match = re.search(r'energy-mode:\s*(\w+)', cli_text)

                if match:
                    mode = match.group(1)

                power_data_equipo.setdefault('Mode', mode)
            elif 'slot' in type:
                slots = self.extractDataBetweenLines(cli_text, 5, 6).split()[0].replace('<', '').replace('>', '').split(
                    ',')
                for slot in slots:
                    if '-' in slot:
                        x, y = slot.split('-')
                        for number in range(int(x), int(y) + 1):
                            board_slots.append(number)
                    else:
                        board_slots.append(slot)
            elif type == 'boards':
                for line in cli_text.splitlines():
                    if 'Description' in line:
                        if 'PIC' in line:
                            name = line.split(',')[-1]
                            type2 = 'PIC'
                        elif 'NPU' in line:
                            name = line.split(',')[-1].split()[-1].replace('(', '').replace(')', '')
                            type2 = 'NPU'
                        elif 'MPU' in line:
                            type2 = 'MPU'
                            type3 = line.split(',')[-1].split()[-1]
                            name = f'MPU {type3}'
                        config_data_equipo = {
                            'name': name,
                            'type': type2
                        }
        if 'adva' in device_name.lower():
            if 'config_power-supply_fan' in type:
                n_powersupply = 0
                cli_text = cli_text.replace(
                    '=================================================================', '')
                cli_text = cli_text.replace(
                    '-----------------------------------------------------------------', '')

                count = 0
                lines = cli_text.splitlines()

                while count < len(lines):
                    line = lines[count]
                    if 'Power Supply Slots' in line:
                        values = lines[count + 1].split()
                        type2 = values[1].split('-')[0]
                        name = values[1].replace('-', '_')
                    count += 1

                config_data_equipo[name] = {
                    'name': name,
                    'type': type2
                }
                n_powersupply += 1
            elif 'config_transceivers' in type:
                lines = cli_text.splitlines()
                count = 0
                while count < len(lines):
                    line = lines[count]
                    trx = ''
                    if 'Port#' in line:
                        n_trx = line.split()[0].split('#')[1]
                        subline = lines[count + 6]

                        for i, part in enumerate(subline.split()):
                            if 'GBASE' in part:
                                trx = part
                                break
                        name = trx
                        if '10G' in trx:
                            type2 = '10G'
                        elif '100G' in trx:
                            type2 = '100G'
                        else:
                            name = '10GBASE-SR'
                            type2 = '10G'

                        config_data_equipo['TRX_' + n_trx] = {
                            'name': name,
                            'type': type2
                        }

                    count += 1
            elif 'power-supply' in type and 'config' not in type:
                cli_text = cli_text.replace(
                    '===========================================================================================', '')
                cli_text = cli_text.replace(
                    '-------------------------------------------------------------------------------------------', '')

                cli_text = os.linesep.join([line for line in cli_text.splitlines() if line])
                power_data_equipo = dict()
                count = 0
                variables = {}

                for line in cli_text.splitlines():
                    if count == 0:
                        variables = line.split()
                    elif count > 2:
                        valores = line.split()
                        temp_dict = dict(zip(variables, valores))
                        psu_name = temp_dict["Inserted"].replace('-', '_')
                        power_data_equipo[psu_name] = temp_dict
                    count += 1
                #power_data[device_name] = power_data_equipo
                #return power_data
            elif 'cpu' in type and 'config' not in type:
                cli_text = self.extractDataBetweenLines(cli_text, 1, 4)
                cpu_rate = cli_text.split(':')[1].strip().rstrip('%')
                power_data_equipo.setdefault('CPU', {}).setdefault('Usage(%)', cpu_rate)
            elif 'fan' in type and 'config' not in type:
                cli_text = self.extractDataBetweenLines(cli_text, 5, 1)
                fan_rate = cli_text.split()[2]
                power_data_equipo.setdefault('FAN', {}).setdefault('Usage(RPM)', fan_rate)
                pass
        if 'juniper' in device_name.lower():
            if 'fan' in type:
                count = 0
                fan_utilization = {}
                variables = []
                averaged_data = {}
                for line in cli_text.splitlines():
                    if count == 0:
                        line = line.replace("% RPM", "%RPM")
                        variables = line.split()
                    else:
                        line = line.strip()
                        parts = line.split()
                        fan_tray = parts[0] + ' ' + parts[1] + ' ' + parts[2]
                        fan = parts[3] + ' ' + parts[4]
                        status = parts[5]
                        percent = parts[6]
                        rpm_value = float(parts[7])
                        values = [f'{fan_tray} {fan}', status, percent, rpm_value]
                        values = dict(zip(variables, values))

                        if fan_tray not in fan_utilization:
                            # Si no existe, crear el array con los valores
                            fan_utilization[fan_tray] = {'%RPM': [percent], 'RPM': [rpm_value]}
                        else:
                            # Si ya existe, añadir el nuevo valor al array correspondiente
                            fan_utilization[fan_tray]['%RPM'].append(percent)
                            fan_utilization[fan_tray]['RPM'].append(rpm_value)

                    count += 1

                for item, values in fan_utilization.items():
                    # Calculamos la media de los valores de '%RPM' y 'RPM'
                    rpm_avg = sum(values['RPM']) / len(values['RPM']) if values['RPM'] else 0
                    rpm_percent_avg = sum([int(rpm.strip('%')) for rpm in values['%RPM']]) / len(values['%RPM']) if \
                        values['%RPM'] else 0
                    averaged_data[item] = {
                        '%RPM': f'{rpm_percent_avg}%',
                        'RPM': rpm_avg
                    }

                power_data_equipo = averaged_data
            elif 'chassis-components' in type:
                variable_actual = None

                cli_text = self.extractDataBetweenLines(cli_text, 12, 1)

                for line in cli_text.splitlines():
                    if line != '':
                        if line.find('System') != -1:
                            variable_actual = "System"
                            power_data_equipo[variable_actual] = {}
                            continue
                        elif line.find('Item') != -1:
                            variable_actual = "Items"
                            power_data_equipo[variable_actual] = {}
                            continue

                        elif variable_actual == 'System':
                            if line.find('Zone') == -1:
                                value, valor = line.split(':')
                                power_data_equipo[variable_actual][value.lstrip(' ')] = valor.lstrip(' ')
                        elif variable_actual == 'Items':
                            if line.find('Fan') != -1:
                                line = ';'.join(line.split())
                                variable, value = [
                                    line.split(';')[0] + line.split(';')[1] + line.split(';')[2] + ' (W)',
                                    line.split(';')[3]]
                                power_data_equipo[variable_actual][variable] = float(value)
                            elif line.find('SFB') != -1 or line.find('FPC') != -1:
                                line = ';'.join(line.split())
                                variable, value = [line.split(';')[0] + line.split(';')[1] + ' (W)', line.split(';')[2]]
                                power_data_equipo[variable_actual][variable] = float(value)
                            elif line.find('RE') != -1:
                                line = ';'.join(line.split())
                                variable, value = [line.split(';')[0] + ' (W)', line.split(';')[1]]
                                power_data_equipo[variable_actual][variable] = float(value)
            elif 'power-supply' in type:
                i = 0
                lines = cli_text.splitlines()
                actual_pem = ''
                power_supplies = {}
                while i < len(lines):
                    line = lines[i]
                    if 'PEM' in line:
                        actual_pem = f'{line.split()[0]}{line.split()[1]}'
                        power_supplies[actual_pem] = {
                            'State': {},
                            'Input': {},
                            'Output': {}
                        }
                    elif 'State' in line:
                        state = line.split()[1]
                        power_supplies[actual_pem]['State'] = state
                        if state == 'Offline':
                            i += 7
                    elif 'Output' in line:
                        variables = line.split()[2:]
                        valores = lines[i + 1].split()
                        valores = [float(valor) for valor in valores]
                        temp_dict = dict(zip(variables, valores))
                        power_supplies[actual_pem]['Output'] = temp_dict
                        i += 1
                    elif 'Input' in line:
                        variables = line.split()[1:]
                        valores = lines[i + 1].split()[2:]
                        valores = [float(valor) for valor in valores]
                        temp_dict = dict(zip(variables, valores))
                        power_supplies[actual_pem]['Input'] = temp_dict
                        i += 1
                    i += 1
                power_data_equipo = power_supplies
            elif 'chassis-config' in type:
                for line in cli_text.splitlines():
                    if 'Routing' in line:
                        type2 = 'RE'
                        name_component = 'RE' + line.split()[2]
                        name = line.split()[-4] + ' ' + line.split()[-3]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'CB' in line:
                        type2 = 'CB'
                        name_component = line.split()[0] + line.split()[1]
                        name = line.split()[-2] + ' ' + line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'FPC' in line:
                        type2 = 'FPC'
                        name_component = line.split()[0] + line.split()[1]
                        name = line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'PEM' in line:
                        type2 = 'PEM'
                        name_component = line.split()[0] + line.split()[1]
                        name = line.split()[-5] + ' ' + line.split()[-4] + ' ' + line.split()[-3] + ' ' + line.split()[
                            -2] + ' ' + line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'Fan Tray' in line:
                        type2 = 'Fan Tray'
                        name_component = line.split()[0] + line.split()[1] + line.split()[2]
                        name = line.split()[-2] + ' ' + line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'SFB' in line:
                        type2 = 'SFB'
                        name_component = line.split()[0] + line.split()[1]
                        name = line.split()[-3] + ' ' + line.split()[-2] + ' ' + line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
                    elif 'TIB' in line:
                        type2 = 'TIB'
                        name_component = line.split()[0]
                        name = line.split()[-3] + ' ' + line.split()[-2] + ' ' + line.split()[-1]
                        config_data_equipo[name_component] = {'name': name, 'type': type2}
            elif 'config-transceivers' in type:
                for line in cli_text.splitlines():
                    slot = line.splitlines()[0].split('/')[-1]
                    if slot == '8':
                        config_data_equipo['TRX_' + slot] = {
                            'name': 'QSFP',
                            'type': '400G'
                        }
                    else:
                        config_data_equipo['TRX_' + slot] = {
                            'name': 'QSFP',
                            'type': '100G'
                        }
        if 'ufispace' in device_name.lower():
            if type == 'config-transceivers':
                count = 0
                lines = cli_text.splitlines()
                while count < len(lines):
                    line = lines[count]
                    if 'Interface' in line and 'breakout' not in line:
                        slot = line.split('/')[-1]
                        if 'Identifier' in lines[count + 1]:
                            name = lines[count + 1].split()[-1]
                            if name == 'QSFP28':
                                type2 = '100G'
                            elif name == 'QSFP_DD':
                                type2 = '400G'
                            config_data_equipo['TRX_' + slot] = {
                                'name': name,
                                'type': type2
                            }
                        else:
                            pass

                    count += 1
            else:
                lines = cli_text.splitlines()
                cli_elements = {
                    'node': "\n".join(lines[22:25]),
                    'power_supplies': "\n".join(lines[12:22]),
                    'cpu': "\n".join(lines[47:70]),
                    'temperature': "\n".join(lines[168:192]),
                    'fan': "\n".join(lines[193:205])
                }

                for key, value in cli_elements.items():
                    if key == 'node':
                        capacity = ''
                        remaining = ''
                        for line in value.splitlines():
                            if 'capacity' in line:
                                capacity = float(line.split()[2].replace("W", ''))
                            elif 'remaining' in line:
                                remaining = float(line.split()[2].replace('W', ''))
                        power = capacity - remaining
                        power_data_equipo['node'] = {
                            'capacity': capacity,
                            'remaining': remaining,
                            'power': power
                        }
                    elif key == 'power_supplies':
                        power_data_equipo['power-supply'] = {}
                        lines = value.splitlines()
                        i = 0
                        psu_list = []
                        while i < len(lines):
                            line = lines[i]
                            if 'psu' in line.lower():
                                name = line.split()[0] + '_' + line.split()[1].replace(':', '')
                                status = lines[i + 1].split()[1]
                                psu = {}
                                if status == 'FAIL':
                                    psu = {
                                        'name': name,
                                        'status': status,
                                        'input-power': None,
                                        'capacity': None
                                    }
                                elif status == 'OK':
                                    power = float(lines[i + 4].split()[2].replace('W', ''))
                                    capacity = float(lines[i + 3].split()[1].replace('W', ''))
                                    psu = {
                                        'name': name,
                                        'status': status,
                                        'input-power': power,
                                        'capacity': capacity
                                    }
                                power_data_equipo['power-supply'][name] = psu
                                i += 4
                            i += 1
                    elif key == 'cpu':
                        i = 0
                        lines = value.splitlines()
                        cpu_usage = []
                        while i < len(lines):
                            line = lines[i]
                            if i > 4:
                                if 'last' in line.lower():
                                    break
                                elif line != '':
                                    cpu_usage.append(float(line.split()[3]))
                            i += 1
                        cpu_average = float(sum(cpu_usage) / len(cpu_usage))
                        power_data_equipo.setdefault('cpu', {}).setdefault('CPU', {}).setdefault('Usage(%)',
                                                                                                 cpu_average)
                    elif key == 'temperature':
                        temp = ''
                        for line in value.splitlines():
                            if 'TEMP_ENV' in line:
                                temp = float(line.split()[3])
                        power_data_equipo.setdefault('temperature', {}).setdefault('Ambient(ºC)', temp)
                    elif key == 'fan':
                        fan_speed = []
                        for line in value.splitlines():
                            if 'RPM' in line and 'YES' in line:
                                fan_speed.append(float(line.split()[7]))
                        fan_average = float(sum(fan_speed) / len(fan_speed))
                        power_data_equipo.setdefault('fan', {}).setdefault('FAN', {}).setdefault('Usage(RPM)',
                                                                                                 fan_average)
        if 'cisco' in device_name.lower():
            if type == 'power-supply':
                lines = cli_text.splitlines()
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if 'Total power input' in line:
                        total_in_power = line.split(':')[1].strip().replace('W', '')
                        power_data_equipo['Total Input Power'] = total_in_power
                    elif 'Total power output' in line:
                        total_out_power = line.split(':')[1].strip().replace('W', '')
                        power_data_equipo['Total Output Power'] = total_out_power
                    elif 'Module' in line:
                        variables = line.split() + ['Status']
                        variables[2] += ' Input'
                        variables[3] += ' Input'
                        variables[4] += ' Output'
                        variables[5] += ' Output'
                        values = lines[i + 2].split()
                        psu = dict(zip(variables, values))
                        power_data_equipo[psu['Module'].split('/')[1]] = psu
                    i += 1
            if type == 'fan':
                lines = cli_text.splitlines()
                i = 0
                fan0 = []
                fan1 = []
                while i < len(lines):
                    line = lines[i]
                    if 'FT' in line:
                        fan0.append(int(line.split()[2]))
                        fan1.append(int(line.split()[3]))
                    i += 1
                power_data_equipo = {
                    'FAN_0': int(sum(fan0) / len(fan0)),
                    'FAN_1': int(sum(fan1) / len(fan1)),
                }
            if type == 'config-all':
                i = 0
                lines = cli_text.splitlines()
                while i < len(lines):
                    line = lines[i]
                    if 'Pluggable' in line:
                        slot = line.split(',')[0].split('/')[-1]
                        if 'QSFP28' in line:
                            name = 'QSFP28'
                            type2 = '100G'
                        elif 'QSFPDD' in line:
                            name = 'QSFPDD'
                            type2 = '400G'
                        config_data_equipo['TRX_' + slot] = {
                            'name': name,
                            'type': type2
                        }
                        i += 2
                    elif 'PM' in line:
                        name = line.split(',')[0].split(':')[1].replace('"', '').split('/')[1]
                        type2 = lines[i + 1].split(':')[1].split(',')[0].strip()
                        config_data_equipo[name] = {
                            'name': type2,
                            'type': 'PSU'
                        }
                        i += 2
                    i += 1

        if config_data_equipo:
            return config_data_equipo
        elif power_data_equipo:
            return power_data_equipo
        elif board_slots:
            return board_slots
        else:
            return 0

    def obtain_power_data(self, device_data, device_name, api_session, test_parameters):
        power_info_cli = self.cli_power_data(device_data, device_name, test_parameters)
        power_info_pdu = {}
        if device_data['pdu'] is not None:
            for ps_name, ps_outlet in device_data['pdu'].items():
                power_info_pdu[ps_name] = self.api_power_data(device_data, device_name, api_session, ps_outlet)
        return power_info_cli, power_info_pdu

    def pdu_to_yang(self, device_name, device_dict, device_dict_pdu):
        power = 0
        for ps_data in device_dict_pdu.values():
            power = power + float(ps_data['PowerWatts']['Reading'])

        device_dict['device-power-information']['power'] = power

    def cli_configuration_data(self, device, device_name, test_parameters):
        """
        Function that makes the CLI call to the device.
        Args:
            device: device parameters
            device_name: name of the device to be consulted
            ssh_client: SSH session with the device

        Returns: dictionary with all obtained energy consumption data

        """
        hostname = device['ip']
        username = device['username']
        password = device['password']
        vendor = device['vendor']
        info = device['info']
        name = info.split(' ')[0] + ' ' + info.split(' ')[1]
        config_data_device = {}
        power_data_device = {}

        if test_parameters.debug_mode:
            logger_cli.info(f'Reading config data for: {device_name}')
        else:
            logger_cli.info('...')

        if vendor.lower() == 'huawei':
            commands = {}
            if info.find("NE40E") != -1:
                if info.find("NE40E V800R022C10") != -1:
                    commands = {
                        'boards-slot': ['display boardinfo slot ?']
                    }
                else:
                    commands = {
                        'chassis-boards': 'display board-power'
                    }
            elif info.find("ATN") != -1:
                if info.find("ATN 950C V800R022C10") != -1:
                    commands = {
                        'chassis-boards': 'display power consumption'
                    }
                else:
                    commands = {
                        'chassis-boards': 'display power slot detail'
                    }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
            power_data_device.setdefault('PSU_13', {}).update(
                {'name': 'PSU Huawei', 'type': 'PSU'})
            power_data_device.setdefault('PSU_14', {}).update(
                {'name': 'PSU Huawei', 'type': 'PSU'})
            '''
            power_data_device.setdefault('TRX_1', {}).update(
                {'name': 'QSFP', 'type': '100G'})
            power_data_device.setdefault('TRX_2', {}).update(
                {'name': 'QSFP', 'type': '100G'})
            '''
        elif vendor.lower() == 'adva':
            commands = {
                'config_power-supply_fan': ['show chassis table'],
                'config_transceivers': ['show port sfp']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    command = f'vtysh -e "{command}" '
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'ufispace':
            commands = {
                'config-transceivers': ['show interface transceiver']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
            power_data_device.setdefault('PSU_1', {}).update(
                {'name': 'AM-2A02P10', 'type': 'PSU'})
        elif vendor.lower() == 'juniper':
            commands = {
                'chassis-config': ['show chassis hardware detail'],
                'config-transceivers': ['show interfaces diagnostics optics | match "Physical interface"']
            }
            threads = []
            for metric, multiple_commands in commands.items():
                time.sleep(1)
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()
        elif vendor.lower() == 'cisco':
            commands = {
                'config-all': ['show inventory all'],
            }
            threads = []
            for metric, multiple_commands in commands.items():
                for command in multiple_commands:
                    thread = threading.Thread(target=self.execute_command_in_thread,
                                              args=(
                                                  command, hostname, username, password, test_parameters,
                                                  power_data_device,
                                                  metric, device_name, info))
                    threads.append(thread)
                    thread.start()

            for thread in threads:
                thread.join()

        return power_data_device

    def complete_devices_configuration(self, test_parameters):
        config_data_devices = {}
        for device_name, device_data in test_parameters.devices_list.items():
            config_data_devices[device_name] = {}
            config_data_device = self.cli_configuration_data(device_data, device_name, test_parameters)
            config_data_devices[device_name] = config_data_device

        test_parameters.config_data_devices = config_data_devices
        for device_name, config in config_data_devices.items():
            elements = []
            trxs = []
            for key, value in config.items():
                if 'TRX' in key:
                    trxs.append('T' + value['type'])
                else:
                    elements.append(key)

            counts = {}
            for element in trxs:
                if element in counts:
                    counts[element] += 1
                else:
                    counts[element] = 1

            results = [f"{count}x{element}" for element, count in counts.items()]

            config_components = elements + results

            test_parameters.configuration[device_name] = ";".join(config_components)

class EnergyCollectorTimeSeriesDB:
    def __init__(self):
        self.url_influxdb = "http://10.152.183.14:8086"
        self.token = "my_admin_token"
        self.org = "uEnergyOrg"
        self.bucket = "time_series_db_pruebas"
    
    def save_influxdb_instantaneous_data(self, device_name, instantaneous_data, test_data):
        logger_cli.info("Inserting instantaneous data in InfluxDB")
        client = InfluxDBClient(url=self.url_influxdb, token=self.token, org=self.org)
        self.insert_data_influxdb(client, device_name, instantaneous_data, test_data)
        client.close()
        return 0
    
    def insert_data_influxdb(self, client, device, instantaneous_data, test_dict):
        utc_now = datetime.now(ZoneInfo('UTC'))
        current_time = utc_now.astimezone(ZoneInfo('Europe/Berlin'))

        points = [Point(device)
                  .field("name", instantaneous_data['device-power-information']["name"])
                  .field("power_device", instantaneous_data['device-power-information']["power"])
                  .field("energy_mode", instantaneous_data['device-power-information']["energy-mode"])
                  .field("energy_efficiency", instantaneous_data['device-power-information']["energy-efficiency"])
                  .time(current_time, WritePrecision.NS),
                  Point(device)
                  .tag("Inst Info", "configuration")
                  .field("boards", instantaneous_data['device-power-information']['configuration']['boards'])
                  .field("transceivers",
                         instantaneous_data['device-power-information']['configuration']['transceivers'])
                  .time(current_time, WritePrecision.NS),
                  Point(device)
                  .tag("Inst Info", "perfomance-metrics")
                  .field("ambient_temperature",
                         instantaneous_data['device-power-information']['performance-metrics']['ambient-temperature'])
                  .field("cpu-load", instantaneous_data['device-power-information']['performance-metrics']['cpu-load'])
                  .field("traffic_type",
                         instantaneous_data['device-power-information']['performance-metrics']['traffic-type'])
                  .field("fan_speed",
                         instantaneous_data['device-power-information']['performance-metrics']['fan-speed'])
                  .field("traffic_throughput",
                         instantaneous_data['device-power-information']['performance-metrics']['traffic-throughput'])
                  .field("traffic_packet_size",
                         instantaneous_data['device-power-information']['performance-metrics']['traffic-packet-size'])
                  .time(current_time, WritePrecision.NS),
                  Point(device)
                  .tag("Inst Info", "Test")
                  .field("DateTime", test_dict["Test"]["DateTime"].astimezone(
                      ZoneInfo('Europe/Berlin')).isoformat())
                  .field("Times", float(test_dict["Test"]["Times"]))
                  .field("TestConfiguration", test_dict["Test"]["TestConfiguration"])
                  .field("DeviceConfiguration", test_dict["Test"]["DeviceConfiguration"])
                  .field("Scenario", test_dict["Test"]["Scenario"])
                  .field("StartTime", test_dict["Test"]["StartTime"])
                  .field("StartDate", test_dict["Test"]["StartDate"])
                  .time(current_time, WritePrecision.NS)]

        for data in instantaneous_data['device-power-information']["boards"]:
            points.append(
                Point(device)
                .tag("Inst Info", "boards")
                .tag("board", data["name"])
                .field("name", data["name"])
                .field("type", data["type"])
                .field("power", data["power"])
                .time(current_time, WritePrecision.NS)
            )
        for data in instantaneous_data['device-power-information']["components"]:
            points.append(
                Point(device)
                .tag("Inst Info", "components")
                .tag("component", data["name"])
                .field("name", data["name"])
                .field("type", data["type"])
                .field("power", data["power"])
                .time(current_time, WritePrecision.NS)
            )
        for data in instantaneous_data['device-power-information']["transceivers"]:
            points.append(
                Point(device)
                .tag("Inst Info", "transceivers")
                .tag("transceiver", data["name"])
                .field("name", data["name"])
                .field("type", data["type"])
                .field("power", data["power"])
                .time(current_time, WritePrecision.NS)
            )

        for data in instantaneous_data['device-power-information']["power-supply"]:
            points.append(
                Point(device)
                .tag("Inst Info", "power-supplies")
                .tag("power_supply", data["name"])
                .field("name", data["name"])
                .field("rated_power", data["rated-power"])
                .field("input_current", data["input-current"])
                .field("input_voltage", data["input-voltage"])
                .field("input_power", data["input-power"])
                .field("output_current", data["output-current"])
                .field("output_voltage", data["output-voltage"])
                .field("output_power", data["output-power"])
                .field("efficiency", data["efficiency"])
                .time(current_time, WritePrecision.NS)
            )

        write_api = client.write_api(write_options=SYNCHRONOUS)
        try:
            write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger_cli.info("Insert instantaneous data in InfluxDB: Successfull")
        except Exception as e:
            logger_cli.info(f"Error: Inserting instantaneous data in InfluxDB: {e}")



    
    def save_csv(self, test_parameters, device_name):
        logger_cli.info("TODO-CSVs: Save instantaneous data in influxDB via API")
        return 0