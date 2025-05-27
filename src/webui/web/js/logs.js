const socket = new WebSocket(`ws://${window.location.hostname}:${window.location.port}/ws/`);
const mensajes = document.getElementById('response_test');

socket.onmessage = (event) => {
  const obj = JSON.parse(event.data);

  // Mostrar mensaje en el log
  const li = document.createElement('li');
  li.textContent = obj.data;
  li.style.listStyle = 'none';

  if (obj.type === 'log') {
    li.style.color = 'gray';
    li.style.fontStyle = 'italic';
  }

  mensajes.appendChild(li);
  mensajes.scrollTop = mensajes.scrollHeight;

  // Si el mensaje es un update de energía
  if (obj.type === 'power_update') {
    const nodeId = obj.id;
    const power = obj.power;

    // Siempre actualizamos el mapa
    realtimePowerMap[nodeId] = power;

    // Solo actualizamos visual si corresponde
    if (showPowerInfo && powerSource === 'realtime') {
      updatePowerDisplay();
    }
  }
};

socket.onerror = () => {
  mensajes.textContent = 'Error en la conexión WebSocket.';
};
