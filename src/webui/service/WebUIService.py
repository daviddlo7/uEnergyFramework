import grpc
from concurrent import futures
from grpc_reflection.v1alpha import reflection
import os
import logging
from flask import Flask, request, jsonify
from webui_pb2_grpc import add_WebUIServicer_to_server
from webui_pb2 import DESCRIPTOR as WEBUI_DESCRIPTOR
from service.WebUIServiceservicerImpl import WebUIServicerImpl
import energycollector_pb2
import energycollector_pb2_grpc
import analytics_pb2
import analytics_pb2_grpc
import require
import json

# Configuración del cliente gRPC para EnergyCollector
ENERGYCOLLECTOR_SERVICE_IP = '10.152.183.12'  # IP del servicio energycollector-service
ENERGYCOLLECTOR_SERVICE_PORT = '50051'
ANALYTICS_SERVICE_IP = '10.152.183.13'
ANALYTICS_SERVICE_PORT = '50051'
# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación Flask
app = Flask(__name__)
app.config['TIMEOUT'] = 86400

def call_energycollector(packetsize, devices, traffic_config,scenario,total_time,traffic_change,packet_change,traffic,database,csv,debug_mode,web_interface):
    """Función que realiza la llamada gRPC al servicio EnergyCollector."""
    try:
        logger.info(f"Conectando a {ENERGYCOLLECTOR_SERVICE_IP}:{ENERGYCOLLECTOR_SERVICE_PORT}")
        with grpc.insecure_channel(f'{ENERGYCOLLECTOR_SERVICE_IP}:{ENERGYCOLLECTOR_SERVICE_PORT}') as channel:
            stub = energycollector_pb2_grpc.EnergyCollectorStub(channel)
            logger.info(f"Enviando solicitud gRPC con parametros.")
            request = energycollector_pb2.TestParameters(devices_names=devices,traffic_configuration=traffic_config,escenario=scenario,total_time=total_time,traffic_change=traffic_change,traffic=traffic, packet_change=packet_change,packet_size=packetsize,db=database,web_interface=web_interface,debug_mode=debug_mode,save_csvs=csv)
            logger.info(f"Enviando solicitud gRPC con parametros2.")
            response = stub.RunTest2(request)
            logger.info(f"Respuesta recibida del servidor gRPC: {response.message}")
            return response.message
    except Exception as e:
        logger.error(f"Error al llamar al servicio gRPC: {e}")
        return {"error": str(e)}

def call_analytics(device):
    try:
        logger.info(f"Conectando a {ANALYTICS_SERVICE_IP}:{ANALYTICS_SERVICE_PORT}")
        with grpc.insecure_channel(f'{ANALYTICS_SERVICE_IP}:{ANALYTICS_SERVICE_PORT}') as channel:
            stub = analytics_pb2_grpc.AnalyticsServiceStub(channel)
            logger.info(f"Enviando solicitud gRPC con parametros.")
            request = analytics_pb2.StaticInformationRequest(device_name=device)
            response = stub.ConsultStaticInformation(request)
        
            return response.result_static_json
    except Exception as e:
        logger.error(f"Error al consultar influxdb: {e}")
        return {"error": str(e)}


@app.route('/run-test', methods=['POST'])
def run_test():
    """Endpoint HTTP para manejar solicitudes desde la aplicación web."""
    try:
        data = request.get_json()
        packetsize = data.get("packet_size","")
        devices = data.get("devices_names","")
        traffic_config = data.get("traffic_configuration", "")
        scenario = data.get("escenario","")
        total_time = data.get("total_time","")
        traffic_change = data.get("traffic_change","")
        packet_change = data.get("packet_change","")
        traffic = data.get("traffic","")
        database = data.get("db","")
        csv = data.get("save_csvs", "")
        debug_mode = data.get("debug_mode","")
        web_interface = data.get("web_interface","")

        # Llamada al servicio gRPC de EnergyCollector
        result = call_energycollector(packetsize, devices, traffic_config,scenario,total_time,traffic_change,packet_change,traffic,database,csv,debug_mode,web_interface)
        return jsonify({"result": result}) # Error or Test Started

    except Exception as e:
        logger.error(f"Error en run-test: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/run-static', methods=['POST'])
def run_static():
    try:
        data = request.get_json()
        device = data.get("device","")

        result = call_analytics(device)
        logger.info(f'resultado es: {result}')
        json_object = json.loads(result)
        logger.info(f'resultado en json es: {json_object}')
        return json_object

    except Exception as e:
        logger.error(f"Error en run-static: {e}")
        return jsonify({"error": str(e)}), 500
class WebUIService:
    """Clase para manejar el servidor gRPC."""

    def __init__(self):
        self.port = os.getenv("GRPC_PORT", "50053")  # Cambiar puerto para evitar conflicto con Flask
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = WebUIServicerImpl()

    def install_servicers(self):
        """Registrar servicios y habilitar reflexión."""
        add_WebUIServicer_to_server(self.servicer, self.server)

        # Habilitar reflexión para herramientas como grpcurl
        service_names = [
            WEBUI_DESCRIPTOR.services_by_name["WebUI"].full_name,
            reflection.SERVICE_NAME,
        ]
        reflection.enable_server_reflection(service_names, self.server)

    def start(self):
        """Iniciar el servidor gRPC."""
        self.install_servicers()
        self.server.add_insecure_port(f"[::]:{self.port}")
        logger.info(f"Servidor gRPC escuchando en puerto {self.port}...")
        self.server.start()

    def stop(self):
        """Detener el servidor gRPC."""
        logger.info("Deteniendo servidor gRPC...")
        self.server.stop(0)

if __name__ == '__main__':
    # Iniciar ambos servidores (Flask y gRPC) en paralelo
    from threading import Thread

    # Iniciar Flask en un hilo separado
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=50052))
    flask_thread.start()

    # Iniciar el servidor gRPC
    grpc_service = WebUIService()
    grpc_service.start()
