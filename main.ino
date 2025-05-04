// C++ code
//


/* Criar uma função que após descobrir a porcentagem de 
umidade do solo consiga decidir o tempo necessário para 
realizar a rega. É preciso saber a quantidade de água 
que sai da bomba por segundo e seja feito o calculo. 
-> Com essa resolução utilizariamos um tempo que deixe 
o solo na condição que preferirmos. Não irá ocorrer 
de o solo ficar sem água ou ficar em excesso. 

1- Entender a utilização do modulo de regulagem de deteccao de umidade*/

unsigned long TempoRega(int SensorDados);
int lerUmidade();
int umidade = 0;
int limiteInferior = 175;
const int pinoSensor = A0;
const int pinoMotor = 6;
const int pinoLed = 12;
const int tempoAgua = 50;

float taxaAumento = 50; // Estimativa de quanto a umidade sobe por segundo
int UmidadeIdeal = 700; // valor alvo

// Fazer os testes quando tiver a parte fisica montada

// Função para calcular tempo para alcançar nível ideal solo
unsigned long calcularTempoRega(int umidadeAtual){ 
  if (umidadeAtual >= UmidadeIdeal){
    return 0;
  }
  float diferenca = UmidadeIdeal - umidadeAtual;
  return (unsigned long)(diferenca / taxaAumento * 1000); // Retorna em milissegundos
   
}

// Função para ler umidade do solo
int lerUmidade(){
  return analogRead(pinoSensor);
}


void setup()
{
  pinMode(umidade, INPUT);
  Serial.begin(9600);
  pinMode(pinoLed, OUTPUT);
  pinMode(pinoMotor, OUTPUT);
}

void loop()
{
  // Loop para verificar umidade do solo.
  for(int i = 0; i<5; i++){
    int umidade = lerUmidade();
    Serial.println(umidade);
  }
  
  // Se a umidade for menor que o limite inferior a bomba é ligada
  if (umidade <= limiteInferior) {
    Serial.println("Ativando bomba para realizar a rega...");
    // Liga o motor e o led
    digitalWrite(pinoMotor, HIGH);
    digitalWrite(pinoLed, HIGH);
    // espera 
    unsigned long tempoEspera = calcularTempoRega(umidade);
    delay(tempoEspera); // 
    // Desliga o motor e o led
    digitalWrite(pinoMotor, LOW);
    digitalWrite(pinoLed, LOW);
  }else{
    // Solo encharcado
    Serial.println("Solo encharcado");
    delay(50000); // Espera 50 segundos até fazer uma nova analise - 2 horas 
  }
  delay(1000); // Delay a little bit to improve simulation performance
}