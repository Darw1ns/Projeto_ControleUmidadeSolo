#define rele 5
#define sensorvcc 10
#define sensorAna A2

// --- AJUSTE AQUI OS NÍVEIS DE UMIDADE ---
const float UMIDADE_PARA_LIGAR = 50.0;
const float UMIDADE_PARA_DESLIGAR = 60.0;

// --- INTERVALOS DE TEMPO ---
const unsigned long DELAY_COM_BOMBA = 5000UL;     // 5 segundos quando a bomba está LIGADA
const unsigned long DELAY_SEM_BOMBA = 8UL * 60UL * 60UL * 1000UL / 3UL; // 8 horas 
//const unsigned long DELAY_SEM_BOMBA = 20000UL; // 20 segundos quando esta desligada para testes. 
bool bombeandoParaIdeal = false;

void setup() {
  Serial.begin(115200);
  pinMode(rele, OUTPUT);
  pinMode(sensorAna, INPUT);
  pinMode(sensorvcc, OUTPUT);

  digitalWrite(rele, HIGH);   // Bomba começa desligada
  digitalWrite(sensorvcc, LOW); // Sensor começa desligado

  Serial.println("Sistema iniciado.");
}

void loop() {
  int umidadeValorAnalogico = 0;
  long somaLeituras = 0;

  digitalWrite(sensorvcc, HIGH);
  delay(1000); // Tempo para estabilizar o sensor

  for (int i = 0; i < 20; i++) {
    umidadeValorAnalogico = analogRead(sensorAna);
    somaLeituras += umidadeValorAnalogico;
    delay(50);
  }

  digitalWrite(sensorvcc, LOW);

  float mediaUmidadeAnalogica = (float)somaLeituras / 20.0;
  float umidadePercent = (1023.0 - mediaUmidadeAnalogica) / 1023.0 * 100.0;
  if (umidadePercent < 0) umidadePercent = 0;
  if (umidadePercent > 100) umidadePercent = 100;

  Serial.print("Umidade Atual: ");
  Serial.print(umidadePercent, 1);
  Serial.println("%");

  if (bombeandoParaIdeal) {
    if (umidadePercent >= UMIDADE_PARA_DESLIGAR) {
      digitalWrite(rele, HIGH); // Desliga a bomba
      bombeandoParaIdeal = false;
      Serial.println("Umidade ideal alcançada. Bomba desligada.");
    } else {
      digitalWrite(rele, LOW);  // Mantém a bomba ligada
      Serial.println("Bombeando para atingir a umidade ideal...");
    }
  } else {
    if (umidadePercent < UMIDADE_PARA_LIGAR) {
      digitalWrite(rele, LOW);  // Liga a bomba
      bombeandoParaIdeal = true;
      Serial.println("Umidade baixa. Iniciando bombeamento.");
    } else {
      digitalWrite(rele, HIGH); // Mantém desligada
      Serial.println("Umidade OK. Bomba desligada.");
    }
  }

  // Delay dinâmico:
  if (bombeandoParaIdeal) {
    delay(DELAY_COM_BOMBA);  // Checa frequentemente se já atingiu a umidade ideal
  } else {
    delay(DELAY_SEM_BOMBA);  // Verifica só 3x ao dia (delay longo)
  }
}

