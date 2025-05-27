document.addEventListener("DOMContentLoaded", () => {
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
