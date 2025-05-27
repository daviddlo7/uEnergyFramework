document.addEventListener("DOMContentLoaded", () => {
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
});
