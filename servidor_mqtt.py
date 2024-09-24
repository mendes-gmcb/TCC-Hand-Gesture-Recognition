import paho.mqtt.client as mqtt
import pandas as pd
import json
import time

# Funções de callback MQTT
def on_message(client, userdata, message):
  payload = message.payload.decode()
  data = json.loads(payload)
  
  # Cria um dicionário para armazenar os dados dos sensores
  sensor_data = {
    "2": [data['2'][0], data['2'][1], data['2'][2], data['2'][3], data['2'][4], data['2'][5]],
    "3": [data['3'][0], data['3'][1], data['3'][2], data['3'][3], data['3'][4], data['3'][5]],
    "4": [data['4'][0], data['4'][1], data['4'][2], data['4'][3], data['4'][4], data['4'][5]],
    "5": [data['5'][0], data['5'][1], data['5'][2], data['5'][3], data['5'][4], data['5'][5]],
    "6": [data['6'][0], data['6'][1], data['6'][2], data['6'][3], data['6'][4], data['6'][5]]
  }
  
  # Adiciona os dados ao DataFrame
  df.loc[len(df)] = [sensor_data["2"], sensor_data["3"], sensor_data["4"], sensor_data["5"], sensor_data["6"]]

# Configurações do broker MQTT
mqtt_broker = "192.168.226.69" # IP do notebook
mqtt_port = 1883
mqtt_topic = "sensor/mpu6050"

# Inicializa o DataFrame com colunas para cada sensor
df = pd.DataFrame(columns=["2", "3", "4", "5", "6"])

# Cria uma instância do cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# Configura callbacks
client.on_message = on_message
# Conecta ao broker MQTT
client.connect(mqtt_broker, mqtt_port, 60)
# Inscreve-se no tópico
client.subscribe(mqtt_topic)


# Loop principal
client.loop_start()

# Coleta de dados por um tempo determinado
time.sleep(2)  # Coleta dados por 60 segundos

client.loop_stop()
client.disconnect()

# Salva os dados em um arquivo JSON
df.to_json('gestos/fechar_mao5.json', orient='records')