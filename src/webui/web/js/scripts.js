import * as pb from './energycollector_pb.js'; // Importamos todo como "pb"
import * as grpcWeb from './energycollector_grpc_web_pb.js'; // Importamos todo como "grpcWeb"

// URL del servicio gRPC configurado en NGINX
const grpcServiceUrl = 'http://localhost/grpc-web/';

// Crear el cliente gRPC desde grpcWeb
const client = new grpcWeb.EnergyCollectorClient(grpcServiceUrl);

function runGrpcTest() {
    // Crear la solicitud gRPC desde pb
    const request = new pb.TestRequest();
    request.setTestData('test_data'); // Configurar el campo test_data

    // Realizar la llamada gRPC al método RunTest
    client.runTest(request, {}, (err, response) => {
        const resultElement = document.getElementById('Result');

        if (err) {
            // Manejo de errores
            console.error('Error en la llamada gRPC:', err.message);
            resultElement.textContent = `Error: ${err.message}`;
        } else {
            // Manejo de respuesta exitosa
            console.log('Respuesta del servidor:', response.getMessage());
            resultElement.textContent = `Respuesta: ${response.getMessage()}`;
        }
    });
}

// Asignar el evento al botón "RunTest"
document.getElementById('RunTest').addEventListener('click', runGrpcTest);
