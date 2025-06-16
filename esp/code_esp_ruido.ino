#include <ESP8266WiFi.h>
#include <PubSubClient.h>


// Configurações Wi-Fi
const char* ssid = "EraldoCesar2";
const char* password = "19611616@Cesar";

// MQTT Broker
const char *mqtt_server = "192.168.0.19";
const char *Topico_Bomba_Status = "irrigacao/bomba/status"; 
const char *Topico_Sensor_Umidade = "irrigacao/sensor_umidade";


// Objetos do Wi-Fi e MQTT
WiFiClient espClient;
PubSubClient client(espClient);

// Variável para armazenar o último estado da bomba e evitar publicações repetidas
String ultimoStatusBomba = "";



void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando-se a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (client.connect("esp8266-cliente")) {
      Serial.println("Conectado");
    } else {
      Serial.print("Erro, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);

}

// Variável global para armazenar os dados recebidos do Arduino
String inputString = ""; 

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // ----- Leitura Serial Mais Robusta -----
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') { // Se o caractere for uma nova linha, a mensagem terminou
      // --- Início do processamento da mensagem ---
      inputString.trim();
      Serial.print("Recebido do Arduino: ");
      Serial.println(inputString);

      // 1. Publicar dados de umidade
      if (inputString.startsWith("Umidade Atual: ")) {
        int startIndex = inputString.indexOf(": ") + 2;
        int endIndex = inputString.indexOf("%");
        if (startIndex > 1 && endIndex > startIndex) {
          String valorUmidade = inputString.substring(startIndex, endIndex);
          valorUmidade.trim();
          Serial.print("Publicando Umidade: ");
          Serial.println(valorUmidade);
          client.publish(Topico_Sensor_Umidade, valorUmidade.c_str(), true);
        }
      }

      // 2. Publicar status da bomba
      String statusAtualDetectado = "";
      if (inputString.indexOf("Iniciando bombeamento") != -1 || inputString.indexOf("Bombeando para atingir") != -1) {
        statusAtualDetectado = "LIGADA";
      } else if (inputString.indexOf("Bomba desligada") != -1) {
        statusAtualDetectado = "DESLIGADA";
      }

      if (statusAtualDetectado != "" && statusAtualDetectado != ultimoStatusBomba) {
        Serial.print("Publicando Status da Bomba: ");
        Serial.println(statusAtualDetectado);
        client.publish(Topico_Bomba_Status, statusAtualDetectado.c_str(), true);
        ultimoStatusBomba = statusAtualDetectado;
      }
      // --- Fim do processamento da mensagem ---
      
      inputString = ""; // Limpa a variável para a próxima mensagem
    } else {
      inputString += inChar; // Adiciona o caractere à string
    }
  }
  // O delay(100) pode ser removido ou mantido, não afeta esta lógica.
}