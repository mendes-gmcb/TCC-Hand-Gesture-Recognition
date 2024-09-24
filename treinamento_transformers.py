import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from sklearn.model_selection import train_test_split
import pandas as pd
import json
import os

# Função para carregar os dados de um arquivo JSON e adicionar a atividade correspondente
def carregar_dados(caminho_arquivo, atividade):
    with open(caminho_arquivo, 'r') as file:
        data = json.load(file)
    
    sequences = []
    for item in data:
        sequence = []
        for sensor_id, values in item.items():
            sequence.append(values)
        sequences.append((sequence, atividade))  # Adicionar atividade como rótulo
    return sequences

# Dataset personalizado para trabalhar com DataLoader
class GestureDataset(Dataset):
    def __init__(self, data, labels):
        self.data = data
        self.labels = labels
        self.label_to_idx = {label: idx for idx, label in enumerate(set(labels))}

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        sequence = torch.tensor(self.data[idx], dtype=torch.float32)
        label = self.label_to_idx[self.labels[idx]]
        return sequence, torch.tensor(label, dtype=torch.long)

# Transformer-based gesture recognition model
class GestureTransformer(nn.Module):
    def __init__(self, input_dim, d_model, nhead, num_layers, num_classes):
        super(GestureTransformer, self).__init__()
        # Camada para mapear os 6 valores dos sensores para a dimensão de embedding
        self.embedding = nn.Linear(input_dim, d_model)
        
        # Usar batch_first=True para que a primeira dimensão seja o batch
        encoder_layers = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)
        self.fc = nn.Linear(d_model, num_classes)

    def forward(self, x):
        # Aplicar a camada de embedding para mapear de 6 para d_model (64)
        x = self.embedding(x)
        
        # Passar os dados pelo transformer encoder
        x = self.transformer_encoder(x)
        
        # Média sobre a dimensão temporal
        x = x.mean(dim=1)
        
        # Camada totalmente conectada para a classificação final
        x = self.fc(x)
        return x

# Função principal para carregar e treinar o modelo
def main():
    # Carregar dados de gestos e preparar rótulos
    arquivos_gestos = {
        './gestos/sem_gesto.json': 'sem_gesto',
        './gestos/sem_gesto2.json': 'sem_gesto',
        './gestos/sem_gesto3.json': 'sem_gesto',
        './gestos/sem_gesto4.json': 'sem_gesto',
        './gestos/sem_gesto5.json': 'sem_gesto',
        './gestos/sem_gesto6.json': 'sem_gesto',
        './gestos/sem_gesto7.json': 'sem_gesto',
        './gestos/sem_gesto8.json': 'sem_gesto',
        './gestos/sem_gesto9.json': 'sem_gesto',
        './gestos/sem_gesto10.json': 'sem_gesto',
        './gestos/sem_gesto11.json': 'sem_gesto',
        './gestos/sem_gesto12.json': 'sem_gesto',
        './gestos/sem_gesto13.json': 'sem_gesto',
        './gestos/sem_gesto14.json': 'sem_gesto',
        './gestos/sem_gesto15.json': 'sem_gesto',
        './gestos/sem_gesto16.json': 'sem_gesto',
        './gestos/sem_gesto17.json': 'sem_gesto',
        './gestos/sem_gesto18.json': 'sem_gesto',
        './gestos/sem_gesto19.json': 'sem_gesto',
        './gestos/sem_gesto20.json': 'sem_gesto',
        './gestos/passar_slide.json': 'passar_slide',
        './gestos/voltar_slide.json': 'voltar_slide',
        './gestos/passarslide2.json': 'passar_slide',
        './gestos/voltarslide2.json': 'voltar_slide',
        './gestos/passarslide3.json': 'passar_slide',
        './gestos/voltarslide3.json': 'voltar_slide',
        './gestos/passarslide4.json': 'passar_slide',
        './gestos/voltarslide4.json': 'voltar_slide',
        './gestos/passarslide5.json': 'passar_slide',
        './gestos/voltarslide5.json': 'voltar_slide',
        './gestos/passarslide6.json': 'passar_slide',
        './gestos/voltarslide6.json': 'voltar_slide',
        './gestos/passarslide7.json': 'passar_slide',
        './gestos/voltarslide7.json': 'voltar_slide',
        './gestos/passarslide8.json': 'passar_slide',
        './gestos/voltarslide8.json': 'voltar_slide',
        './gestos/passarslide9.json': 'passar_slide',
        './gestos/voltarslide9.json': 'voltar_slide',
        './gestos/voltarslide10.json': 'voltar_slide',
        './gestos/passarslide10.json': 'passar_slide',
        './gestos/voltarslide11.json': 'voltar_slide',
        './gestos/passarslide11.json': 'passar_slide',
        './gestos/voltarslide12.json': 'voltar_slide',
        './gestos/passarslide12.json': 'passar_slide',
        './gestos/voltarslide13.json': 'voltar_slide',
        './gestos/passarslide13.json': 'passar_slide',
        './gestos/voltarslide14.json': 'voltar_slide',
        './gestos/passarslide14.json': 'passar_slide',
        './gestos/voltarslide15.json': 'voltar_slide',
        './gestos/passarslide15.json': 'passar_slide',
        './gestos/voltarslide16.json': 'voltar_slide',
        './gestos/passarslide16.json': 'passar_slide',
        './gestos/voltarslide17.json': 'voltar_slide',
        './gestos/passarslide17.json': 'passar_slide',
        './gestos/voltarslide18.json': 'voltar_slide',
        './gestos/passarslide18.json': 'passar_slide',
        './gestos/voltarslide19.json': 'voltar_slide',
        './gestos/passarslide19.json': 'passar_slide',
        './gestos/voltarslide20.json': 'voltar_slide',
        './gestos/passarslide20.json': 'passar_slide',
        './gestos/fechar_mao.json': 'fechar_mao',
        './gestos/fechar_mao2.json': 'fechar_mao',
        './gestos/fechar_mao3.json': 'fechar_mao',
        './gestos/fechar_mao4.json': 'fechar_mao',
        
    }

    sequencias = []
    rotulos = []

    for caminho, gesto in arquivos_gestos.items():
        sequencias_gesto = carregar_dados(caminho, gesto)
        # print(sequencias_gesto)
        for seq, rotulo in sequencias_gesto:
            sequencias.append(seq)
            rotulos.append(rotulo)

    # Dividir os dados em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(sequencias, rotulos, test_size=0.3, random_state=42)

    # Configurar parâmetros do modelo
    input_dim = 6   # Número de características: accX, accY, accZ, gyrX, gyrY, gyrZ
    d_model = 64       # Dimensão de embedding
    nhead = 4       # Número de cabeças de atenção
    num_layers = 3  # Número de camadas do transformer
    num_classes = 4  # Número de classes de gestos

    # Criar datasets e dataloaders
    train_dataset = GestureDataset(X_train, y_train)
    test_dataset = GestureDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32)
    
    # Inicializar o modelo
    model = GestureTransformer(input_dim=input_dim, d_model=d_model, nhead=nhead, num_layers=num_layers, num_classes=num_classes)
    
    # print(model)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Treinar o modelo
    num_epochs = 10
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for sequences, labels in train_loader:
            # print(sequences)
            optimizer.zero_grad()
            outputs = model(sequences)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(train_loader)}")

    # Salvar o modelo treinado
    torch.save(model.state_dict(), 'modelo_transformer_v2.pt')
    print("Modelo salvo como 'modelo_transformer.pt'")

    # Avaliar o modelo
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for sequences, labels in test_loader:
            outputs = model(sequences)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = correct / total
    print(f"Acurácia: {accuracy}")

if __name__ == "__main__":
    main()
