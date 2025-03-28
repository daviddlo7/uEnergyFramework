async function ejecutarComando() {
  const resultadoDiv = document.getElementById('resultado');
  resultadoDiv.textContent = 'Ejecutando comando...';

  try {
      const response = await fetch('http://backend-service:3000/ejecutar-comando', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device: 'example_device' })
      });

      if (!response.ok) throw new Error('Error al ejecutar el comando');
      const resultado = await response.text();
      resultadoDiv.textContent = `Resultado: ${resultado}`;
  } catch (error) {
      console.error(error);
      resultadoDiv.textContent = 'Ocurrió un error al ejecutar el comando.';
  }
}
