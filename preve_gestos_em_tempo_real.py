import torch
import paho.mqtt.client as mqtt
import json
import pyautogui  # Para controle de slides
import time

from collections import defaultdict
from treinamento_transformers import GestureTransformer  # Importe o modelo transformer do seu script
import numpy as np

# Parâmetros do modelo (devem corresponder aos usados no treinamento)
input_dim = 6  # accX, accY, accZ, gyrX, gyrY, gyrZ
d_model = 64
nhead = 4
num_layers = 3
num_classes = 2  # Quantidade de gestos possíveis

sensor_ids = ['2', '3', '4', '5', '6']  # IDs dos sensores disponíveis

# Limiar de movimento para detectar se o usuário está parado ou se moveu
MOVEMENT_THRESHOLD = 10000  # Ajuste conforme necessário
DELAY_BETWEEN_ACTIONS = 1  # Tempo de espera entre ações (em segundos)

# Carregar o modelo transformer treinado
model = GestureTransformer(input_dim=input_dim, d_model=d_model, nhead=nhead, num_layers=num_layers, num_classes=num_classes)
model.load_state_dict(torch.load('modelos/modelo_transformer_vfinal.pt'))
model.eval()  # Coloca o modelo em modo de avaliação

sensor_predictions = defaultdict(list)
last_action_time = time.time()  # Armazena o tempo da última ação

# Função de controle de slides
def control_slides(predicted_class):
    global last_action_time
    current_time = time.time()
    
    # Verifica se já passou o tempo de espera
    if current_time - last_action_time >= DELAY_BETWEEN_ACTIONS:
        if predicted_class == 0:  # Classe '1' corresponde ao gesto 'passar_slide'
            print("Passando slide...")
            pyautogui.press("right")  # Simula pressionar a tecla "direita" para passar o slide
        elif predicted_class == 1:  # Classe '0' corresponde ao gesto 'voltar_slide'
            print("Voltando slide...")
            pyautogui.press("left")  # Simula pressionar a tecla "esquerda" para voltar o slide
        
        # Atualiza o tempo da última ação
        last_action_time = current_time

# Função para calcular a magnitude dos dados de movimento (acelerômetro + giroscópio)
def calculate_magnitude(sensor_data):
    accX, accY, accZ, gyrX, gyrY, gyrZ = sensor_data
    acc_magnitude = np.sqrt(accX**2 + accY**2 + accZ**2)
    gyr_magnitude = np.sqrt(gyrX**2 + gyrY**2 + gyrZ**2)
    return acc_magnitude + gyr_magnitude

# Função para verificar se há movimento com base no limiar
def has_movement(sensor_data):
    magnitude = calculate_magnitude(sensor_data)
    return magnitude > MOVEMENT_THRESHOLD

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
    
    # Extrair dados de cada sensor individualmente
    for sensor_id in sensor_ids:
        if sensor_id in data:
            sensor_data = data[sensor_id]  # Pega os dados do sensor específico
            
            # Verifica se há movimento
            if has_movement(sensor_data):
                # Converter os dados do sensor para tensor e ajustar dimensão (batch_size, seq_len, input_dim)
                features = torch.tensor([sensor_data], dtype=torch.float32).unsqueeze(0)
                
                # Faz a previsão usando o modelo treinado
                with torch.no_grad():
                    prediction = model(features)

                # Selecionar a classe prevista
                predicted_class = torch.argmax(prediction, dim=1).item()
                
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
