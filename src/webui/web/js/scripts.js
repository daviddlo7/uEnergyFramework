import { EnergyCollectorClient } from '../../src/energycollector/generated/energycollector_grpc_web_pb';
import { TestRequest } from '../../src/energycollector/generated/energycollector_pb';

// Crear el cliente gRPC-Web apuntando al proxy
const client = new EnergyCollectorClient('http://localhost:80/grpc-web');

async function runGrpcTest() {
    const request = new TestRequest();
    request.setTestData("test_data"); // Establece los datos de prueba

    client.runTest(request, {}, (err, response) => {
        if (err) {
            console.error('Error en la solicitud:', err.message);
            document.getElementById('resultado').textContent = "Error: " + err.message;
        } else {
            console.log('Respuesta del servidor:', response.getMessage());
            document.getElementById('resultado').textContent = "Respuesta: " + response.getMessage();
        }
    });
}

// Vincula la función al evento click del botón
document.getElementById('RunTest').addEventListener('click', runGrpcTest);