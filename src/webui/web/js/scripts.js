console.log("scripts.js cargado");
document.addEventListener("DOMContentLoaded", () => {
  // RUN STATIC
  const device = document.getElementById('devices2');
  device.addEventListener("change", async () => {
    const value = device.value;
    if (value !== "") {
      try {
        const response = await fetch('/run-static', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device: value }),
        });

        if (response.ok) {
          const result = await response.json();
          mostrarTablas(result);
        } else {
          resetStaticFields();
        }
      } catch (error) {
        resetStaticFields();
      }
    } else {
      resetStaticFields();
    }
  });

  function mostrarTablas(data) {
    const mainObj = Object.values(data)[0];

    const generalTable = document.getElementById("general-table").querySelector("tbody");
    const componentsTable = document.getElementById("components-table").querySelector("tbody");

    generalTable.innerHTML = "";
    componentsTable.innerHTML = "";

    const generales = ["typical-power", "max-traffic", "max-power", "efficiency", "nominal-power"];
    generales.forEach(key => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${key}</td><td>${mainObj[key] ?? 'No Data'}</td>`;
      generalTable.appendChild(tr);
    });

    const keys = ["power-supply", "board", "transceiver"];
    keys.forEach(grupo => {
      const elementos = mainObj[grupo] || {};
      Object.entries(elementos).forEach(([nombre, datos]) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${grupo} - ${nombre}</td>
                        <td>${datos["typical-power"] ?? '-'}</td>
                        <td>${datos["nominal-power"] ?? '-'}</td>`;
        componentsTable.appendChild(tr);
      });
    });
  }

  function resetStaticFields() {
    document.getElementById("general-table").querySelector("tbody").innerHTML = "";
    document.getElementById("components-table").querySelector("tbody").innerHTML = "";
  }

  // RUN TEST
  document.getElementById('startTestForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    function parseArray(input) {
      if (input && input.startsWith("[") && input.endsWith("]")) {
        return input.slice(1, -1).split(",").map(Number);
      }
      return [parseFloat(input)];
    }

    const logMode = document.getElementById('log-mode').checked;
    const devices = Array.from(document.getElementById('devices').selectedOptions).map(opt => opt.value);
    const trafficConfig = document.getElementById('traffic-config').value;
    const scenario = document.getElementById('scenario').value;
    const totalTime = parseFloat(document.getElementById('total-time')?.value || "1");
    const trafficChange = parseFloat(document.getElementById('traffic-change').value || "0");
    const traffic = parseArray(document.getElementById('traffic').value);
    const packageChange = parseFloat(document.getElementById('package-change').value || "0");
    const packetSize = parseArray(document.getElementById('packet-size').value);
    const database = document.getElementById('database').value;
    const debugMode = document.getElementById('debug-mode').checked;
    const webInterface = document.getElementById('web-interface').checked;
    const csv = document.getElementById('csv').checked;
    const responseElement = document.getElementById('response');

    if (
      devices.length === 0 || !trafficConfig || !scenario ||
      isNaN(totalTime) || totalTime <= 0 ||
      isNaN(trafficChange) || !traffic || traffic.length === 0 ||
      isNaN(packageChange) || !packetSize || packetSize.length === 0 ||
      !database
    ) {
      responseElement.style.color = 'red';
      responseElement.textContent = "Complete the form.";
      return;
    } else {
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
          log_mode: logMode,
          web_interface: webInterface
        }),
      });

      if (response.ok) {
        const result = await response.json();
        responseElement.textContent = `Respuesta del servidor: ${result.message}`;
      } else if (response.status === 504) {
        responseElement.textContent = "Test started";
      } else {
        responseElement.textContent = `Error: ${response.statusText}`;
      }
    } catch (error) {
      responseElement.textContent = `Error de conexión: ${error.message}`;
    }
  });
});

// WEBSOCKET
const socket = new WebSocket(`ws://${window.location.hostname}:${window.location.port}/ws/`);
const mensajes = document.getElementById('response_test');

socket.onmessage = (event) => {
  const obj = JSON.parse(event.data);
  const li = document.createElement('li');
  li.textContent = obj.data;
  li.style.listStyle = 'none';
  if (obj.type === 'log') {
    li.style.color = 'gray';
    li.style.fontStyle = 'italic';
  }
  mensajes.appendChild(li);
};

socket.onerror = () => {
  mensajes.textContent = 'Error en la conexión WebSocket.';
};
