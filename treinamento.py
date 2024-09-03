import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import json
import os
import joblib

# Função para carregar os dados de um arquivo JSON e adicionar a atividade correspondente
def carregar_dados(caminho_arquivo, atividade):
    with open(caminho_arquivo, 'r') as file:
        data = json.load(file)
    
    rows = []
    for item in data:
        for sensor_id, values in item.items():
            row = {"sensor_id": sensor_id, "accX": values[0], "accY": values[1], "accZ": values[2], 
                    "gyrX": values[3], "gyrY": values[4], "gyrZ": values[5], "atividade": atividade}
            rows.append(row)
    
    return pd.DataFrame(rows)

# Lista de arquivos e seus respectivos gestos
arquivos_gestos = {
    './gestos/passar_slide.json': 'passar_slide',
    './gestos/voltar_slide.json': 'voltar_slide',
    './gestos/abrir_mao.json': 'abrir_mao',
    './gestos/fechar_mao.json': 'fechar_mao'
}

# Inicializar um DataFrame vazio
df_total = pd.DataFrame()

# Carregar e concatenar os dados de cada arquivo
for caminho, gesto in arquivos_gestos.items():
    df_gesto = carregar_dados(caminho, gesto)
    df_total = pd.concat([df_total, df_gesto], ignore_index=True)

# Separar características e rótulos
X = df_total[["accX", "accY", "accZ", "gyrX", "gyrY", "gyrZ"]]
y = df_total["atividade"]

# Dividir o conjunto de dados
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Treinar o modelo
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Avaliar o modelo
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Acurácia: {accuracy}")

# Salvar o modelo
joblib.dump(model, 'modelo_movimentos.pkl')
