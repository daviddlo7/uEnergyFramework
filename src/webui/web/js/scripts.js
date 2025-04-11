document.getElementById('grpcForm').addEventListener('submit', async (event) => {
    event.preventDefault(); // Evita que la página se recargue
    function parseArray(input) {
      if (input && input.startsWith("[") && input.endsWith("]")) {
        // Convertimos la cadena de texto en un array de flotantes
        return input.slice(1, -1).split(",").map(Number);
      }
      return [parseFloat(input)]; // Si no es un array, lo convertimos a float
    }
    const devices = Array.from(document.getElementById('devices').selectedOptions).map(opt => opt.value); 
    const trafficConfig = document.getElementById('traffic-config').value; 
    const scenario = document.getElementById('scenario').value; 
    const totalTime = parseFloat(document.getElementById('total-time').value);
    const trafficChange = parseFloat(document.getElementById('traffic-change').value); 
    const traffic = parseArray(document.getElementById('traffic').value); 
    const packageChange = parseFloat(document.getElementById('package-change').value); 
    const packetSize = parseArray(document.getElementById('packet-size').value); 
    const database = document.getElementById('database').value; 
    const debugMode = document.getElementById('debug-mode').checked; 
    const webInterface = document.getElementById('web-interface').checked; 
    const csv = document.getElementById('csv').checked; 
    const responseElement = document.getElementById('response');
    console.log(devices)
    console.log(trafficConfig)
    console.log(scenario)
    console.log(totalTime)
    console.log(trafficChange)
    console.log(traffic)
    console.log(packageChange)
    console.log(packetSize)
    console.log(database)
    
    if (
      devices.length === 0 || 
      !trafficConfig || 
      !scenario || 
      isNaN(totalTime) || totalTime === "" || totalTime <= 0 ||
      isNaN(trafficChange) || trafficChange === "" || trafficChange < 0 || 
      !traffic || traffic.length === 0 ||
      isNaN(packageChange) || packageChange === "" || packageChange < 0 || 
      !packetSize || packetSize.length === 0 || 
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
          devices_names: devices,
          traffic_configuration:trafficConfig,
          escenario:scenario,
          total_time:totalTime,
          traffic_change:trafficChange,
          traffic:traffic,
          packet_change:packageChange,
          packet_size: packetSize,
          db: database,
          save_csvs: csv,
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
        const response = await fetch('/run-static', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            device: value
          }), // Envía los datos del formulario como JSON
        });
    
        if (response.ok) {
          const result = await response.json();
          document.getElementById('response_static').textContent = `Respuesta del servidor: ${JSON.stringify(result)}`;
        } else {
          document.getElementById('response_static').textContent = `Error: ${response.statusText}`;
        }
      } catch (error) {
        document.getElementById('response_static').textContent = `Error de conexión: ${error.message}`;
      }
    }
  });
});
  