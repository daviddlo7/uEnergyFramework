document.getElementById('grpcForm').addEventListener('submit', async (event) => {
    event.preventDefault(); // Evita que la página se recargue
    const devices = Array.from(document.getElementById('devices').selectedOptions).map(opt => opt.value); 
    const trafficConfig = document.getElementById('traffic-config').value; 
    const scenario = document.getElementById('scenario').value; 
    const totalTime = document.getElementById('total-time').value; 
    const trafficChange = document.getElementById('traffic-change').value; 
    const traffic = document.getElementById('traffic').value; 
    const packageChange = document.getElementById('package-change').value; 
    const packetSize = document.getElementById('packet-size').value; 
    const database = document.getElementById('database').value; 
    const debugMode = document.getElementById('debug-mode').checked; 
    const webInterface = document.getElementById('web-interface').checked; 
    const csv = document.getElementById('csv').checked; 
    const responseElement = document.getElementById('response');
    
    if (
      devices.length === 0 || 
      !trafficConfig || 
      !scenario || 
      !totalTime || 
      !trafficChange || 
      !traffic || 
      !packageChange || 
      !packetSize || 
      !database 
      ) {
          // Mostramos mensaje en rojo
          responseElement.style.color = 'red'; // Cambiar el color del texto
          responseElement.textContent = "complete the form";
          return; // Salimos de la función
      }
    
    try {
      const response = await fetch('/run-test', { // Llamada al endpoint /run-test
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          devices: devices,
          traffic_config:trafficConfig,
          scenario:scenario,
          total_time:totalTime,
          traffic_change:trafficChange,
          traffic:traffic,
          packet_change:packageChange,
          packet_Size: packetSize,
          dataBase: database,
          csv: csv,
          debug_mode:debugMode,
          web_interface:webInterface
         }), // Envía los datos del formulario como JSON
      });
  
      if (response.ok) {
        const result = await response.json();
        document.getElementById('response').textContent = `Respuesta del servidor: ${result.message}`;
      } else {
        document.getElementById('response').textContent = `Error: ${response.statusText}`;
      }
    } catch (error) {
      document.getElementById('response').textContent = `Error de conexión: ${error.message}`;
    }
});

document.addEventListener("DOMContentLoaded",  () => {
  const device = document.getElementById('devices2');
  device.addEventListener("change", async () => {
    const value = device.value;
    if (value != ""){
      try {
        const response = await fetch('/run-static', { // Llamada al endpoint /run-test
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            device: value
          }), // Envía los datos del formulario como JSON
        });
    
        if (response.ok) {
          const result = await response.json();
          document.getElementById('response_static').textContent = result.result;
        } else {
          document.getElementById('response_static').textContent = `Error: ${response.statusText}`;
        }
      } catch (error) {
        document.getElementById('response_static').textContent = `Error de conexión: ${error.message}`;
      }
    }
  });
});
  