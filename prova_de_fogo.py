import joblib
import paho.mqtt.client as mqtt
import json

# Carregar o modelo treinado
model = joblib.load('modelo_movimentos.pkl')

# Função de callback para quando uma mensagem é recebida
def on_message(client, userdata, message):
    payload = message.payload.decode()
    data = json.loads(payload)
    
    # Extrai os dados dos sensores específicos
    sensor_data = [
        data['2'][0], data['2'][1], data['2'][2],  # accX, accY, accZ do sensor 2
        data['2'][3], data['2'][4], data['2'][5],  # gyrX, gyrY, gyrZ do sensor 2
        data['3'][0], data['3'][1], data['3'][2],  # accX, accY, accZ do sensor 3
        data['3'][3], data['3'][4], data['3'][5],  # gyrX, gyrY, gyrZ do sensor 3
        data['4'][0], data['4'][1], data['4'][2],  # accX, accY, accZ do sensor 4
        data['4'][3], data['4'][4], data['4'][5],  # gyrX, gyrY, gyrZ do sensor 4
        data['5'][0], data['5'][1], data['5'][2],  # accX, accY, accZ do sensor 5
        data['5'][3], data['5'][4], data['5'][5],  # gyrX, gyrY, gyrZ do sensor 5
        data['6'][0], data['6'][1], data['6'][2],  # accX, accY, accZ do sensor 6
        data['6'][3], data['6'][4], data['6'][5]   # gyrX, gyrY, gyrZ do sensor 6
    ]
    
    # Ajusta as features para previsão
    features = [sensor_data]
    
    # Faz a previsão usando o modelo treinado
    prediction = model.predict(features)
    print(f"Movimento previsto: {prediction[0]}")

# Configurações do broker MQTT
mqtt_broker = "192.168.75.69"
mqtt_port = 1883
mqtt_topic = "sensor/mpu6050"

# Inicializa o cliente MQTT
client = mqtt.Client()
client.on_message = on_message

# Conecta ao broker MQTT e inscreve-se no tópico
client.connect(mqtt_broker, mqtt_port, 60)
client.subscribe(mqtt_topic)

# Loop principal
client.loop_forever()
