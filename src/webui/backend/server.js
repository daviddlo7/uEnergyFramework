const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 3000;

// Middleware para parsear JSON y CORS
app.use(express.json());
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  next();
});

// Ruta para ejecutar grpcurl
app.post('/ejecutar-comando', (req, res) => {
  const { device } = req.body;
  console.log(`Comando recibido para el dispositivo: ${device}`);
  // Comando con la IP fija (10.152.183.12:50051)
  const comando = `grpcurl -plaintext -d '{"device": "${device}"}' 10.152.183.12:50051 energycollector.EnergyCollector/RunTest`;

  exec(comando, (error, stdout, stderr) => {
    if (error) return res.status(500).send(`Error: ${error.message}`);
    res.send(`Comando ejecutado para el dispositivo: ${device}`);
  });
});

app.listen(port, () => console.log('Backend listo en puerto 3000'));
