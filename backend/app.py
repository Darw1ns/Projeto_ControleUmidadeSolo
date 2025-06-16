import sqlite3
import paho.mqtt.client as mqtt
from flask import Flask, jsonify
from flask_cors import CORS
import datetime

# --- Configurações do MQTT---
MQTT_BROKER_HOST = "192.168.0.19" # ip do broker
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_SENSOR = "irrigacao/sensor_umidade"
MQTT_TOPIC_BOMBA_STATUS = "irrigacao/bomba/status"

BD_NOME = 'irrigacao_data.db'

# --- Inicialização do Flask 
app = Flask(__name__)
CORS(app)
# --- Configurações e Estado Global ---
vazao_bomba = 6.67 #ml/s
tempo_bomba_ligada = None   # Guardará o datetime de quando a bomba foi ligada
is_pump_on = False    # Flag para indicar se a bomba está atualmente considerada ligada



# --- Funções do Banco de Dados ---
def adicionar_registro_consumo(timestamp_str, quantidade_ml):
    conexao = None
    try:
        conexao = sqlite3.connect(BD_NOME)
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO consumo_agua (timestamp, quantidade_ml) VALUES (?, ?)", (timestamp_str, quantidade_ml))
        conexao.commit()
        print(f"Registro adicionado: {timestamp_str}, {quantidade_ml}ml")
    except sqlite3.Error as e:
        print(f"Erro ao inserir no banco de dados: {e}")
    finally:
        if conexao:
            conexao.close()

# Função para calcular o consumo
def calcular_consumo(payload_bomba_status, client_mqtt=None):
    global tempo_bomba_ligada, is_pump_on # informa que usa variavel global
   
    agora = datetime.datetime.now()
    timestamp_formatado = agora.strftime("%Y-%m-%d %H:%M:%S")

    print(f"[{timestamp_formatado}] Recebido status da bomba: {payload_bomba_status}")
    if payload_bomba_status == "LIGADA":
        if not is_pump_on:
            tempo_bomba_ligada = agora
            is_pump_on = True
            print(f"[{timestamp_formatado}] Bomba LIGADA. Registrando tempo de início: {tempo_bomba_ligada.strftime('%H:%M:%S')}.")
        else:
            # Bomba já estava ligada, talvez uma mensagem duplicada ou reinício do ESP
            print(f"[{timestamp_formatado}] Bomba já estava registrada como LIGADA desde {tempo_bomba_ligada.strftime('%H:%M:%S') if tempo_bomba_ligada else 'tempo desconhecido'}. Nenhuma ação adicional.")
    elif payload_bomba_status == "DESLIGADA":
        if is_pump_on and tempo_bomba_ligada is not None:
            duracao_timedelta = agora - tempo_bomba_ligada
            duracao_em_segundos = duracao_timedelta.total_seconds()

            if duracao_em_segundos < 0:
                print(f"[{timestamp_formatado}] ERRO: Duração negativa detectada. Tempo LIGADA: {tempo_bomba_ligada}, Tempo DESLIGADA: {agora}. Resetando estado.")
                is_pump_on = False
                pump_on_time = None
                return # Sai da função para evitar cálculos errados

            consumo_ml = duracao_em_segundos * vazao_bomba
            consumo_ml_arrendondado = round(consumo_ml, 2)


            print(f"[{timestamp_formatado}] Bomba DESLIGADA.")
            print(f"  Tempo ligada: {duracao_em_segundos:.2f} segundos.")
            print(f"  Vazão configurada: {vazao_bomba} ml/s.")
            print(f"  Consumo calculado: {consumo_ml_arrendondado:.2f} ml.")  
            adicionar_registro_consumo(timestamp_formatado, consumo_ml_arrendondado)

            # Resetar o estado para o próximo ciclo
            tempo_bomba_ligada = None
            is_pump_on = False
    elif not is_pump_on:
        print(f"[{timestamp_formatado}] Bomba DESLIGADA recebida, mas não estava registrada como LIGADA. Nenhuma ação de cálculo.")
    elif pump_on_time is None and is_pump_on:
        print(f"[{timestamp_formatado}] Bomba DESLIGADA recebida, registrada como LIGADA, mas sem tempo de início. Resetando estado.")
        is_pump_on = False
    else:
        print(f"[{timestamp_formatado}] Status da bomba não reconhecido: '{payload_bomba_status}'")           

     

    

# --- Lógica MQTT ---
def on_connect(client, userdata, flags, rc, properties=None): # Adicionado 'properties=None' para compatibilidade com paho-mqtt v2.x
    if rc == 0:
        print(f"Conectado ao MQTT Broker: {MQTT_BROKER_HOST}")                   # O QUE É RC? 0 a conexão é bem sucedida. 
        # Subscreve ao tópico assim que conectar
        client.subscribe(MQTT_TOPIC_BOMBA_STATUS)
        print(f"Subscrito ao tópico: {MQTT_TOPIC_BOMBA_STATUS}")
    else:
        print(f"Falha ao conectar ao MQTT, código de retorno: {rc}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    print(f"Mensagem recebida no tópico '{msg.topic}': {payload_str}")


    if msg.topic == MQTT_TOPIC_BOMBA_STATUS:
        calcular_consumo(payload_str, client) 



# Configura o cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) # Especificando a versão da API de Callback
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# --- Rota Flask --- #
@app.route('/')
def hello():
    return "Servidor de irrigação rodando!"

@app.route('/consumo', methods=['GET'])
def get_consumo():
    conexao = None
    try:
        print(f"DEBUG: Verificando sqlite3.Row. Tipo: {type(sqlite3.Row)}, Conteúdo: {sqlite3.Row}") 

        conexao = sqlite3.connect(BD_NOME)
        conexao.row_factory = sqlite3.Row # Garante que as linhas retornadas se comportem como dicionarios
        cursor  = conexao.cursor()
        cursor.execute("SELECT timestamp, quantidade_ml FROM consumo_agua ORDER BY timestamp DESC LIMIT 20")
        registros = cursor.fetchall()
        # Converte os registros para uma lista de dicionários para facilitar o JSON
        # Para depuração
        if registros:
            print(f"Tipo do primeiro registro (row): {type(registros[0])}")
            print(f"Primeiro registro (row): {registros[0]}")
            if hasattr(registros[0], 'keys'):
                print(f"Chaves do primeiro registro: {registros[0].keys()}")
            else:
                print("Primeiro registro não tem o método keys(), provavelmente não é sqlite3.Row")

        lista_registros = [dict(row) for row in registros]
        return jsonify(lista_registros)
    
    except sqlite3.Error as e:
        print(f"Erro SQLite em /consumo: {e}") # Log mais detalhado
        return jsonify({"erro": f"Erro no banco de dados: {e}"}), 500
    except Exception as e: # Captura outros erros inesperados
        print(f"Erro inesperado em /consumo: {e}") # Log mais detalhado
        import traceback
        traceback.print_exc() # Imprime o traceback completo no console do servidor
        return jsonify({"erro": f"Erro inesperado no servidor: {e}"}), 500
    finally:
        if conexao:
            conexao.close()

@app.route('/consumo_mensal', methods=['GET'])
def get_consumo_mensal():
    conexao = None
    try:
        conexao = sqlite3.connect(BD_NOME) # BD_NOME é o nome do seu arquivo de banco
        conexao.row_factory = sqlite3.Row # Para facilitar o acesso às colunas pelo nome
        cursor = conexao.cursor()

        # Query SQL para somar o consumo por mês/ano
        # A função strftime('%Y-%m', timestamp) extrai o ano e mês (ex: '2025-05')
        query = """
            SELECT 
                strftime('%Y-%m', timestamp) as mes_ano, 
                SUM(quantidade_ml) as consumo_total_ml
            FROM consumo_agua
            GROUP BY mes_ano
            ORDER BY mes_ano DESC; 
        """
        # O 'ORDER BY mes_ano DESC' traz os meses mais recentes primeiro

        cursor.execute(query)
        registros_mensais = cursor.fetchall()

        # Converte os resultados para uma lista de dicionários
        lista_consumo_mensal = [dict(row) for row in registros_mensais]

        return jsonify(lista_consumo_mensal)

    except sqlite3.Error as e:
        print(f"Erro SQLite em /api/consumo_mensal: {e}")
        return jsonify({"erro": f"Erro no banco de dados ao buscar consumo mensal: {e}"}), 500
    except Exception as e:
        print(f"Erro inesperado em /api/consumo_mensal: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro inesperado no servidor: {e}"}), 500
    finally:
        if conexao:
            conexao.close()

# --- Função Principal ---
def main():
    try:
        print(f"Tentando conectar ao borker MQTT em {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        # Inicia o loop do MQTT em uma thread separada para não bloquear o Flask (se for usar Flask ativamente)
        # Se for só o script MQTT, mqtt_client.loop_forever() é suficiente.
        mqtt_client.loop_start()
        print("Cliente MQTT inciado e escutando em segundo plano")
        print("Para testar a API de visualização, acesse: http://localhost:5000/consumo")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False) # debug=False em produção

    except KeyboardInterrupt:
        print("Encerrando...")
    except Exception as e:
        print(f"Erro ao iniciar a aplicação: {e}")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Cliente MQTT desconectado.")

if __name__ == '__main__':
    main()  