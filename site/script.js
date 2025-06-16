 // Conectando ao broker via WebSocket
  const  client = mqtt.connect("ws://192.168.0.19:9001"); // use IP do broker se estiver em outro PC
  client.on("connect", function () {
  console.log("Conectado ao broker MQTT");
  client.subscribe("irrigacao/sensor_umidade", function (err) {
  if (!err) {
  console.log("Inscrito no tópico sensor/umidade");
  }
 });
  });
          
  client.on("message", function (topic, message) {
    // Converte a mensagem para string e exibe com %
    var umidadeStr = message.toString();
    document.getElementById("umidade").innerText = "Nível: "+ umidadeStr + "%";
  
    // Converte a mensagem para número
    var umidade = parseFloat(umidadeStr);
  
    // Oculta todos os estados primeiro
    document.querySelectorAll('.estado').forEach(function(el) {
      el.style.display = 'none';
    });
  
    // Mostra o estado correspondente
    if (umidade > 80) {
      document.getElementById('solo-muito-umido').style.display = 'block';
    } else if (umidade >60 && umidade <80) {
      document.getElementById('solo-feliz').style.display = 'block';
    } else {
      document.getElementById('solo-seco').style.display = 'block';
    }
  });
  


// Função para buscar e exibir o consumo do mês atual
async function carregarConsumoMensal() {
    const elementoConsumoMensal = document.getElementById('consumo');
    
    try {
        // Faz a requisição para a API do Flask
        const response = await fetch('http://192.168.0.19:5000/consumo_mensal'); // Use o caminho completo se necessário: http://localhost:5000/api/consumo_mensal
        
        if (!response.ok) {
            // Se a resposta da API não for bem-sucedida (ex: erro 500)
            elementoConsumoMensal.textContent = 'Erro ao carregar dados.';
            console.error('Erro na API:', response.status, await response.text());
            return;
        }
        
        const dadosMensais = await response.json(); // Converte a resposta para JSON
        
        if (dadosMensais.length === 0) {
            elementoConsumoMensal.textContent = 'Nenhum dado de consumo encontrado.';
            return;
        }

        // Determinar o mês/ano atual no formato AAAA-MM
        const dataAtual = new Date();
        const mesAtualString = dataAtual.getFullYear() + '-' + String(dataAtual.getMonth() + 1).padStart(2, '0');
        
        // Procurar os dados do mês atual na resposta da API
        // A API retorna os meses em ordem decrescente, então o primeiro pode ser o mais recente
        // Ou podemos procurar especificamente pelo mês atual
        let consumoDoMesAtual = 0;
        const dadosDoMesAtual = dadosMensais.find(item => item.mes_ano === mesAtualString);

        if (dadosDoMesAtual) {
            consumoDoMesAtual = dadosDoMesAtual.consumo_total_ml;
        } else {
            // Se não houver dados para o mês atual, podemos mostrar o do último mês com dados,
            // ou uma mensagem específica. Por simplicidade, aqui mostraremos 0 ou o último disponível.
            // Para mostrar o último mês com dados (se houver algum dado):
            if (dadosMensais.length > 0) {
                 // Como está ordenado por DESC, o primeiro é o mais recente
                // elementoConsumoMensal.textContent = `${dadosMensais[0].consumo_total_ml.toFixed(2)} ml (Mês: ${dadosMensais[0].mes_ano})`;
                // Vamos focar em achar o mês atual primeiro
                console.log(`Não foram encontrados dados para o mês atual (${mesAtualString}). Exibindo 0ml.`);
            }
        }
        
        elementoConsumoMensal.textContent = `${consumoDoMesAtual.toFixed(2)} ml`;

    } catch (error) {
        elementoConsumoMensal.textContent = 'Falha ao buscar dados.';
        console.error('Erro ao buscar consumo mensal:', error);
    }
}

// Chamar a função quando a página terminar de carregar
window.addEventListener('DOMContentLoaded', carregarConsumoMensal);
// Ou, se preferir que espere tudo (imagens, etc.):
// window.onload = carregarConsumoMensal