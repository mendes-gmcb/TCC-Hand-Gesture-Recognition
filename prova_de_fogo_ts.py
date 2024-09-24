import torch
import paho.mqtt.client as mqtt
import json
import pyautogui  # Para controle de slides
import time

from collections import defaultdict
from treinamento_transformers import GestureTransformer  # Importe o modelo transformer do seu script

# Parâmetros do modelo (devem corresponder aos usados no treinamento)
input_dim = 6  # accX, accY, accZ, gyrX, gyrY, gyrZ
d_model = 64
nhead = 4
num_layers = 3
num_classes = 4  # Quantidade de gestos possíveis

sensor_ids = ['2', '3', '4', '5', '6']  # IDs dos sensores disponíveis

# Carregar o modelo transformer treinado
model = GestureTransformer(input_dim=input_dim, d_model=d_model, nhead=nhead, num_layers=num_layers, num_classes=num_classes)
model.load_state_dict(torch.load('modelo_transformer_v2.pt'))
model.eval()  # Coloca o modelo em modo de avaliação

sensor_predictions = defaultdict(list)

# Função de controle de slides
def control_slides(predicted_class):
    if predicted_class == 1:  # Classe '1' corresponde ao gesto 'passar_slide'
        print("Passando slide...")
        pyautogui.press("right")  # Simula pressionar a tecla "direita" para passar o slide
        # time.sleep(5)
    elif predicted_class == 0:  # Classe '0' corresponde ao gesto 'voltar_slide'
        print("nulo...")
    elif predicted_class == 2:
        pyautogui.press("left")  # Simula pressionar a tecla "esquerda" para voltar o slide
        print("Voltando slide...")
        # time.sleep(5)
    elif predicted_class == 3:
        print("fecha a mão...")
        exit()
        
        

# Função para verificar se todos os sensores concordam com o mesmo gesto
def consensus_gesture():
    all_predictions = []
    for sensor_id in sensor_ids:
        if sensor_predictions[sensor_id]:
            all_predictions.append(sensor_predictions[sensor_id][-1])  # Pega a última previsão de cada sensor
    
    # Verifica se todos os sensores fizeram a mesma previsão
    if len(all_predictions) == len(sensor_ids) and all(pred == all_predictions[0] for pred in all_predictions):
        return all_predictions[0]  # Retorna o gesto em consenso
    return None

# Função de callback para quando uma mensagem é recebida
def on_message(client, userdata, message):
    payload = message.payload.decode()
    data = json.loads(payload)
    
    print(f"Received: {data}")

    # Extrair dados de cada sensor individualmente
    for sensor_id in sensor_ids:
        # Verifica se o sensor está nos dados recebidos
        if sensor_id in data:
            sensor_data = data[sensor_id]  # Pega os dados do sensor específico
            # print(sensor_data)

            # Converter os dados do sensor para tensor e ajustar dimensão (batch_size, seq_len, input_dim)
            features = torch.tensor([sensor_data], dtype=torch.float32).unsqueeze(0)
            # print(features.shape)

            # Faz a previsão usando o modelo treinado
            with torch.no_grad():
                prediction = model(features)

            # Selecionar a classe prevista
            predicted_class = torch.argmax(prediction, dim=1).item()
            print(f"Sensor {sensor_id} - Movimento previsto: {predicted_class}")
            
            # Armazenar a previsão do sensor
            sensor_predictions[sensor_id].append(predicted_class)
            
    # Verificar se todos os sensores concordam com o mesmo gesto
    gesture = consensus_gesture()
    if gesture is not None:
        print(f"Todos os sensores concordam com o gesto: {gesture}")
        control_slides(gesture)

        # Limpar as previsões após a ação
        sensor_predictions.clear()

# Configurações do broker MQTT
mqtt_broker = "192.168.226.69"
mqtt_port = 1883
mqtt_topic = "sensor/mpu6050"

# Inicializa o cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

# Conecta ao broker MQTT e inscreve-se no tópico
client.connect(mqtt_broker, mqtt_port, 60)
client.subscribe(mqtt_topic)

# Loop principal
client.loop_forever()
