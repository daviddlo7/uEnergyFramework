document.addEventListener("DOMContentLoaded", function() {
    async function runTest() {
        const requestData = { test_data: "test_data" };

        try {
            const response = await fetch("http://10.152.183.12:50051/energycollector.EnergyCollector/RunTest", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error("Error en la solicitud: " + response.statusText);
            }

            const responseData = await response.json();
            console.log("Respuesta del servidor:", responseData);

            // Mostrar resultado en el div
            document.getElementById('resultado').textContent = `Respuesta: ${responseData.message}`;
        } catch (error) {
            console.error("Error en la solicitud:", error);
            document.getElementById('resultado').textContent = "Error: No se recibió respuesta del servicio.";
        }
    }

    // Vincula la función runTest al evento click del botón
    document.getElementById('runTestButton').addEventListener('click', runTest);
});
