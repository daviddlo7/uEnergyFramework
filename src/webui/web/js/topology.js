let topologyData = null;
let topologyType = null; // 'ietf' or 'tfs'
let topologyRawData = null;
let simulation = null;

function populateDeviceSelect(nodes) {
  const deviceSelect = document.getElementById("devices");
  if (!deviceSelect) return;
  deviceSelect.innerHTML = '';
  nodes.forEach(node => {
    const opt = document.createElement("option");
    opt.value = node.id;
    opt.textContent = node.name === node.id ? node.name : `${node.name} (${node.id})`;
    deviceSelect.appendChild(opt);
  });
}

function populateStaticDeviceSelect(nodes) {
  const deviceSelect = document.getElementById("devices2");
  if (!deviceSelect) return;
  deviceSelect.innerHTML = '';
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = "-- Select a device --";
  deviceSelect.appendChild(defaultOption);
  nodes.forEach(node => {
    const opt = document.createElement("option");
    opt.value = node.id;
    opt.textContent = node.name === node.id ? node.name : `${node.name} (${node.id})`;
    deviceSelect.appendChild(opt);
  });
}

function renderTopology(original) {
  console.log("📦 renderTopology() recibido:");
  console.log("  🔹 nodes:", original.nodes);
  console.log("  🔸 links:", original.links);

  const width = 800;
  const height = 500;
  const container = document.getElementById('topology-graph');
  if (!container) {
    console.error("❌ No se encontró #topology-graph");
    return;
  }

  const graph = document.getElementById('topology-graph');
  const panel = document.getElementById('mode-panel');
  const text = document.getElementById('topology-text');

  if (graph) graph.innerHTML = '';
  if (text) text.innerHTML = '<p style="color: gray; margin: 0;"></p>';

  const nodes = original.nodes.map(n => ({ ...n }));
  const links = original.links.map(l => ({ ...l }));

  const keySet = topologyType === 'ietf'
    ? new Set(nodes.map(n => n.name))
    : new Set(nodes.map(n => n.id));

  const missingNodes = links
    .flatMap(l => [l.source, l.target])
    .filter(key => !keySet.has(key));

  if (missingNodes.length > 0) {
    console.error("❌ Missing nodes in graph:", [...new Set(missingNodes)]);
    alert("❌ Some links reference unknown nodes:\n" + [...new Set(missingNodes)].join(', '));
    return;
  }

  const svg = d3.select('#topology-graph')
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links)
      .id(d => topologyType === 'ietf' ? d.name : d.id)
      .distance(120))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2));

  const link = svg.append('g')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', '#888')
    .attr('stroke-width', 2)
    .on('click', (event, d) => {
      showLinkDetails(d);
    });

  const node = svg.append('g')
    .selectAll('circle')
    .data(nodes)
    .enter()
    .append('circle')
    .on('click', (event, d) => {
      showNodeDetails(d);
    })
    .attr('r', 15)
    .attr('fill', '#00bcd4')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  const label = svg.append('g')
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text(d => d.name)
    .attr('font-size', 12)
    .attr('dx', 20)
    .attr('dy', 5);

  const powerLabels = svg.append('g')
    .selectAll('text.power-label')
    .data(nodes)
    .enter()
    .append('text')
    .attr('class', 'power-label')
    .attr('font-size', 12)
    .attr('fill', 'green')
    .attr('text-anchor', 'middle');

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node
      .attr('cx', d => d.x).attr('cy', d => d.y);
    label
      .attr('x', d => d.x).attr('y', d => d.y);
    powerLabels
      .attr('x', d => d.x)
      .attr('y', d => d.y - 25)
      .text(d => showPowerInfo && d.power !== undefined ? `${d.power}W` : '');
  });

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x; d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
  }
}



const staticPowerMap = {};
let showPowerInfo = false;

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById('show-power-toggle')?.addEventListener('change', (e) => {
    showPowerInfo = e.target.checked;
    updatePowerDisplay();
  });

  document.getElementById('upload-topology').addEventListener('click', () => {
    const fileInput = document.getElementById('topology-file');
    const file = fileInput.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
      try {
        const raw = JSON.parse(e.target.result);

        if (raw['ietf-network:networks']) {
          const networks = raw['ietf-network:networks'].network;
          const nodes = [];
          const links = [];

          networks.forEach(net => {
            (net.node || []).forEach(n => {
              const id = n['node-id']?.trim();
              const name = n['ietf-l3-unicast-topology:l3-node-attributes']?.name?.trim();
              if (!id || !name) return;
              nodes.push({ id, name, power: Math.floor(Math.random() * 100) });
            });

            (net['ietf-network-topology:link'] || []).forEach(l => {
              const id = l['link-id'];
              if (id.includes(' - ')) {
                const [srcRaw, dstRaw] = id.split(' - ');
                const [source, source_interface] = srcRaw.trim().split(' ');
                const [target, target_interface] = dstRaw.trim().split(' ');

                links.push({
                  source,
                  target,
                  source_interface,
                  target_interface,
                  label: id
                });
              }
            });
          });

          topologyRawData = raw;
          topologyData = { nodes, links };
          topologyType = 'ietf';

          nodes.forEach(n => {
            staticPowerMap[n.id] = Math.floor(Math.random() * 100);
          });

          const nodeList = nodes.map(n => ({ id: n.id, name: n.name }));
          populateDeviceSelect(nodeList);
          populateStaticDeviceSelect(nodeList);

          alert("✅ Topology (IETF) loaded successfully.");
          const selectedMode = document.getElementById('topology-mode')?.value;
          if (selectedMode) showOnlyModePanel(selectedMode);
        }

        else if (Array.isArray(raw.devices) && Array.isArray(raw.links)) {
          topologyRawData = raw;
          const nodes = raw.devices.map(d => {
            const id = d.device_id.device_uuid.uuid.trim();
            const name = d.name?.trim();
            return { id, name, power: Math.floor(Math.random() * 100) };
          });

          const links = raw.links.map(l => {
            const src = l.link_endpoint_ids[0].device_id.device_uuid.uuid.trim();
            const dst = l.link_endpoint_ids[1].device_id.device_uuid.uuid.trim();
            return { source: src, target: dst };
          });

          topologyData = { nodes, links };
          topologyType = 'tfs';
          nodes.forEach(n => {
            staticPowerMap[n.id] = Math.floor(Math.random() * 100); // valor simulado
          });

          console.log("TOPOLOGY TYPE:", topologyType);
          populateDeviceSelect(nodes);
          populateStaticDeviceSelect(nodes);
          alert("✅ Topology (TFS) loaded successfully.");
          const selectedMode = document.getElementById('topology-mode')?.value;
          if (selectedMode) showOnlyModePanel(selectedMode);
        }

        else {
          alert("❌ Unsupported topology format.");
          topologyData = null;
          topologyType = null;
        }

      } catch (err) {
        console.error("Error parsing the JSON file:", err);
        alert("❌ Failed to parse the JSON file.");
        topologyData = null;
        topologyType = null;
      }
    };

    reader.readAsText(file);
  });

  document.getElementById('topology-mode').addEventListener('change', () => {
    const selectedMode = document.getElementById('topology-mode').value;
    const box = document.getElementById('topology-box');
    const panel = document.getElementById('mode-panel');

    box.style.display = 'flex';
    panel.style.display = 'block';

    if (!topologyData) {
      if (selectedMode === 'test') {
        const defaultDevices = [
          { id: 'HL5_1_2_Adva', name: 'HL5_1_2_Adva', power: Math.floor(Math.random() * 100) },
          { id: 'HL4_5_1_Huawei', name: 'HL4_5_1_Huawei', power: Math.floor(Math.random() * 100) },
          { id: 'HL_Ufispace', name: 'HL_Ufispace', power: Math.floor(Math.random() * 100) },
          { id: 'HL_Juniper', name: 'HL_Juniper', power: Math.floor(Math.random() * 100) },
          { id: 'HL_Cisco', name: 'HL_Cisco', power: Math.floor(Math.random() * 100) }
        ];
        topologyData = { nodes: defaultDevices, links: [] };
        populateDeviceSelect(defaultDevices);
        populateStaticDeviceSelect(defaultDevices);
      } else {
        populateDeviceSelect([]);
        populateStaticDeviceSelect([]);
      }

      showOnlyModePanel(selectedMode);
      return;
    }

    if (['topology', 'test', 'telemetry', 'dynamic'].includes(selectedMode)) {
      renderTopology(topologyData);

      populateDeviceSelect(topologyData.nodes);
      populateStaticDeviceSelect(topologyData.nodes);

      showOnlyModePanel(selectedMode);
    }
  });
});


function showNodeDetails(d) {
  const panel = document.getElementById('topology-text');
  if (!panel) return;

  let html = '';

  if (topologyType === 'tfs') {
    const device = topologyRawData.devices.find(dev =>
      dev.device_id.device_uuid.uuid === d.id
    );

    if (!device) {
      panel.innerHTML = `<p>Device not found</p>`;
      return;
    }

    const name = device.name;
    const uuid = device.device_id.device_uuid.uuid;
    const endpoints = (
      device.device_config?.config_rules || []
    ).flatMap(rule => {
      if (rule.custom?.resource_key === "_connect/settings") {
        return rule.custom.resource_value.endpoints.map(ep => ep.name);
      }
      return [];
    });

    html = `
      <strong>Name:</strong> ${name}<br>
      <strong>UUID:</strong> ${uuid}<br>
      <strong>Endpoints:</strong><br>
      <ul>${endpoints.map(e => `<li>${e}</li>`).join('')}</ul>
    `;
  }

  else if (topologyType === 'ietf') {
    const allNetworks = topologyRawData["ietf-network:networks"].network || [];
    const node = allNetworks
      .flatMap(n => n.node || [])
      .find(n => n["node-id"] === d.id);

    if (!node) {
      panel.innerHTML = `<p>Node not found</p>`;
      return;
    }

    const name = node["ietf-l3-unicast-topology:l3-node-attributes"]?.name || d.id;
    const nodeId = node["node-id"];
    const endpoints = (node["ietf-network-topology:termination-point"] || []).map(tp => tp["tp-id"]);

    html = `
      <strong>Name:</strong> ${name}<br>
      <strong>ID:</strong> ${nodeId}<br>
      <strong>Endpoints:</strong><br>
      <ul>${endpoints.map(e => `<li>${e}</li>`).join('')}</ul>
    `;
  }

  panel.innerHTML = html;
}

function showLinkDetails(d) {
  const panel = document.getElementById('topology-text');
  if (!panel) return;

  // Helper: mostrar nombre preferido
  const getDisplayName = x => {
    if (typeof x === 'object') {
      return x.name || x.id || '[object]';
    }
    return x || '[undefined]';
  };

  let html = `<strong>Link</strong><br>`;
  html += `<strong>Source:</strong> ${getDisplayName(d.source)}<br>`;
  html += `<strong>Target:</strong> ${getDisplayName(d.target)}<br>`;

  if ('source_interface' in d || 'target_interface' in d) {
    html += `<strong>Source Interface:</strong> ${d.source_interface || '-'}<br>`;
    html += `<strong>Target Interface:</strong> ${d.target_interface || '-'}<br>`;
  }

  if (d.label) {
    html += `<strong>Label:</strong> ${d.label}<br>`;
  }

  panel.innerHTML = html;
}

function showOnlyModePanel(mode) {
  document.querySelectorAll('.mode-panel-content').forEach(el => el.style.display = 'none');
  const selectedPanel = document.getElementById(`panel-${mode}`);
  if (selectedPanel) selectedPanel.style.display = 'flex';
}

function calculateTopologyPowerConsumption() {
  const output = document.getElementById('topology-power-output');
  if (output) output.value = '...';
}

function calculatePathPowerConsumption() {
  const output = document.getElementById('path-power-output');
  if (output) output.value = '...';
}

function switchDynamicTopology() {
  alert("🌀 Switching topology... (placeholder)");
  // Aquí irá la lógica de cambiar de topología (día/noche)
}

function calculateDynamicTopologyPower() {
  const output = document.getElementById('dynamic-topology-power-output');
  if (output) output.value = '...';
}

function updatePowerDisplay() {
  if (!topologyData) return;

  const svg = d3.select('#topology-graph svg');
  if (svg.empty()) {
    console.warn("⚠️ No SVG found, rendering topology again.");
    renderTopology(topologyData);
    return;
  }

  svg.selectAll('text.power-label')
    .text(d => showPowerInfo && d.power !== undefined ? `${d.power}W` : '');
}
