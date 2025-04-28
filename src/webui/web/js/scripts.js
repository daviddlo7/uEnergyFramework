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
      }else{
        responseElement.style.color = 'black';
      }
    
      try {
        const response = await fetch('/run-test', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                devices_names: devices,
                traffic_configuration: trafficConfig,
                escenario: scenario,
                total_time: totalTime,
                traffic_change: trafficChange,
                traffic: traffic,
                packet_change: packageChange,
                packet_size: packetSize,
                db: database,
                save_csvs: csv,
                debug_mode: debugMode,
                web_interface: webInterface
            }),
        });
    
    
        if (response.ok) {
            const result = await response.json();
            document.getElementById('response').textContent = `Respuesta del servidor: ${result.message}`;
        } else {
          if (response.status === 504) {
              document.getElementById('response').textContent = 'Test started';
          } else {
              document.getElementById('response').textContent = `Error: ${response.statusText}`;
          }
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
          document.getElementById('response_static').textContent = ""; 
          //document.getElementById('response_static').textContent = `Respuesta del servidor: ${JSON.stringify(result)}`;
          mostrarTablas(result);
        } else {
          document.getElementById('response_static').textContent = `Error: ${response.statusText}`;
        }
      } catch (error) {
        document.getElementById('response_static').textContent = `Error de conexión: ${error.message}`;
      }
    }
  });
  function mostrarTablas(data) {
    const contenedor = document.getElementById("response_static");
    contenedor.innerHTML = ""; // Limpiar anteriores

    const mainObj = Object.values(data)[0];
    if (!mainObj || typeof mainObj !== "object") {
      contenedor.textContent = "No hay datos válidos para mostrar.";
      return;
    }

    // Tabla de componentes
    const tablaComponentes = document.createElement("table");
    tablaComponentes.border = "1";
    tablaComponentes.style.borderCollapse = "collapse";
    tablaComponentes.style.marginBottom = "20px";
    tablaComponentes.style.width = "100%";

    const header = tablaComponentes.insertRow();
    ["Elements", "Name", "Nominal Power", "Typical Power"].forEach(texto => {
      const th = document.createElement("th");
      th.textContent = texto;
      th.style.padding = "6px";
      th.style.backgroundColor = "#f0f0f0";
      header.appendChild(th);
    });

    Object.entries(mainObj).forEach(([grupo, valor]) => {
      if (typeof valor === "object" && !Array.isArray(valor)) {
        const tienePotencias = Object.values(valor).some(v =>
          v && typeof v === "object" && ("nominal-power" in v || "typical-power" in v)
        );

        if (tienePotencias) {
          Object.entries(valor).forEach(([nombreElemento, datos]) => {
            if (typeof datos === "object") {
              const fila = tablaComponentes.insertRow();
              fila.insertCell().textContent = grupo;
              fila.insertCell().textContent = nombreElemento;
              fila.insertCell().textContent = datos["nominal-power"] ?? "-";
              fila.insertCell().textContent = datos["typical-power"] ?? "-";
            }
          });
        }
      }
    });

    contenedor.appendChild(tablaComponentes);

    // Tabla de campos generales
    const tablaGenerales = document.createElement("table");
    tablaGenerales.border = "1";
    tablaGenerales.style.borderCollapse = "collapse";
    tablaGenerales.style.width = "100%";

    const header2 = tablaGenerales.insertRow();
    ["Parameters", "Value"].forEach(texto => {
      const th = document.createElement("th");
      th.textContent = texto;
      th.style.padding = "6px";
      th.style.backgroundColor = "#f0f0f0";
      header2.appendChild(th);
    });

    Object.entries(mainObj).forEach(([clave, valor]) => {
      if (typeof valor !== "object" || Array.isArray(valor)) {
        const fila = tablaGenerales.insertRow();
        fila.insertCell().textContent = clave;
        fila.insertCell().textContent = valor;
      }
    });

    contenedor.appendChild(tablaGenerales);
  }
});

const socket = new WebSocket('ws://webui.uenergyframework/ws/');
const mensajes = document.getElementById('response_test');

socket.onmessage = (event) => {
            const obj = JSON.parse(event.data);
            const li = document.createElement('li');
            li.textContent =  obj.data;
            li.style.listStyle = 'none';
            mensajes.appendChild(li);
};

socket.onerror = (error) => {
            mensajes.textContent = 'Error en la conexión WebSocket.';
};

