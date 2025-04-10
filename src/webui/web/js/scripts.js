document.getElementById('grpcForm').addEventListener('submit', async (event) => {
    event.preventDefault(); // Evita que la página se recargue
    const testData = document.getElementById('testData').value;
  
    try {
      const response = await fetch('/run-test', { // Llamada al endpoint /run-test
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_data: testData }), // Envía los datos del formulario como JSON
      });
  
      if (response.ok) {
        const result = await response.json();
        document.getElementById('response').textContent = `Respuesta del servidor: ${result.result}`;
      } else {
        document.getElementById('response').textContent = `Error: ${response.statusText}`;
      }
    } catch (error) {
      document.getElementById('response').textContent = `Error de conexión: ${error.message}`;
    }
  });
  