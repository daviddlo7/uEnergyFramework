import * as pb from './energycollector_pb.js';
import * as grpcWeb from './energycollector_grpc_web_pb.js';

const grpcServiceUrl = 'http://localhost/grpc-web/';

const client = new grpcWeb.EnergyCollectorClient(grpcServiceUrl);

function runGrpcTest() {
    const request = new pb.TestRequest();
    request.setTestData('test_data');

    client.runTest(request, {}, (err, response) => {
        const resultElement = document.getElementById('Result');

        if (err) {
            console.error('Error en la llamada gRPC:', err.message);
            resultElement.textContent = `Error: ${err.message}`;
        } else {
            console.log('Respuesta del servidor:', response.getMessage());
            resultElement.textContent = `Respuesta: ${response.getMessage()}`;
        }
    });
}

document.getElementById('RunTest').addEventListener('click', runGrpcTest);
