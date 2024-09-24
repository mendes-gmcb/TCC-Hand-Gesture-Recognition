
#include <Arduino.h>
#include <Wire.h>
#include <MPU6050.h>
#include <ESP8266WiFi.h>

#include <PubSubClient.h>

// Configurações do Wi-Fi
const char* ssid = "Gabriel Mendes";
const char* password = "mendes123@*";

// Configurações do MQTT
const char* mqtt_broker = "192.168.226.69";  // Substitua pelo IP correto do seu notebook
const int mqtt_port = 1883;
const char* mqtt_topic = "sensor/mpu6050";
int failedPublishes = 0;

// Configurações dos sensores
#define MPUADDR 0x68
#define TCAADDR 0x70
#define SENSOR_RANGE_START 2
#define SENSOR_RANGE_END 6
#define BAUDRATE 460800

const uint8_t portArray[] = {16, 5, 4, 0, 2, 14, 12, 13};
const String dPortMap[] = {"D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"};

struct sensorData {
  int16_t accX, accY, accZ;
  int16_t gyrX, gyrY, gyrZ;
};

// Globais
uint8_t sdaPort, sclPort;
MPU6050 sensor(MPUADDR);
sensorData offsets[8];
WiFiClient espClient;
PubSubClient client(espClient);

// Funções
bool findConnection();
void multiplexer_select(uint8_t i);
void calibrate_sensor(uint8_t i);
void setMPU6050scales(uint8_t Gyro, uint8_t Accl);
void setup_wifi();
void reconnect();

void setup() {
  Serial.begin(BAUDRATE);
  Serial.println("\n\nGesture framework glove starting up.");

  setup_wifi();
  client.setServer(mqtt_broker, mqtt_port);

  while (!findConnection()) {}
  Serial.print("Connection to multiplexer found on SDA:");
  Serial.print(dPortMap[sdaPort]);
  Serial.print(" SCL:");
  Serial.println(dPortMap[sclPort]);

  for (uint8_t i = SENSOR_RANGE_START; i <= SENSOR_RANGE_END; i++) {
    multiplexer_select(i);
    Serial.print("Sensor "); Serial.print(i); Serial.print(": MPU6050 connection ");
    sensor.initialize();
    setMPU6050scales(MPU6050_GYRO_FS_1000, MPU6050_ACCEL_FS_4);
    Serial.println(sensor.testConnection() ? "successful" : "failed");
    calibrate_sensor(i);
  }
  Serial.println("Setup complete.");
  delay(2500);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  sensorData data;
  String json = "{";
  
  for (uint8_t i = SENSOR_RANGE_START; i <= SENSOR_RANGE_END; i++) {
    multiplexer_select(i);
    sensor.getMotion6(&data.accX, &data.accY, &data.accZ, &data.gyrX, &data.gyrY, &data.gyrZ);

    data.accX -= offsets[i].accX;
    data.accY -= offsets[i].accY;
    data.accZ -= offsets[i].accZ;
    data.gyrX -= offsets[i].gyrX;
    data.gyrY -= offsets[i].gyrY;
    data.gyrZ -= offsets[i].gyrZ;

    json += "\"" + String(i) + "\":[";
    json += String(data.accX) + ",";
    json += String(data.accY) + ",";
    json += String(data.accZ) + ",";
    json += String(data.gyrX) + ",";
    json += String(data.gyrY) + ",";
    json += String(data.gyrZ);
    json += "],";
  }
  json.remove(json.length() - 1);  // Remove a última vírgula
  json += "}";

  Serial.print("Tamanho do JSON: ");
  Serial.println(json.length());
  Serial.println("Tentando publicar: " + json);
  bool publishSuccess = client.publish(mqtt_topic, json.c_str());

  if (publishSuccess) {
    Serial.println("Publicação bem-sucedida");
    failedPublishes = 0;
  } else {
    failedPublishes++;
    Serial.println("Falha na publicação MQTT. Tentativa: " + String(failedPublishes));
  }
  
  delay(25);  // Ajuste conforme necessário para controlar a taxa de envio
}

void setup_wifi() {
  delay(10);
  Serial.println("Conectando ao WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conexão MQTT...");
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("conectado");
    } else {
      Serial.print("falhou, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

bool findConnection() {
  for (uint8_t i = 0; i < sizeof(portArray); i++) {
    for (uint8_t j = 0; j < sizeof(portArray); j++) {
      if (i != j) {
        Wire.begin(portArray[i], portArray[j]);
        Wire.beginTransmission(TCAADDR);
        byte error = Wire.endTransmission();
        if (!error) {
          sdaPort = i;
          sclPort = j;
          return true;
        }
      }
    }
  }
  return false;
}

void multiplexer_select(uint8_t i) {
  if (i > 7) return;
  Wire.beginTransmission(TCAADDR);
  Wire.write(1 << i);
  Wire.endTransmission();
}

void calibrate_sensor(uint8_t sensorId) {
  multiplexer_select(sensorId);
  sensorData calData;
  int32_t accX = 0, accY = 0, accZ = 0, gyrX = 0, gyrY = 0, gyrZ = 0;

  for (uint8_t i = 0; i < 100; i++) {    
    sensor.getMotion6(&calData.accX, &calData.accY, &calData.accZ, &calData.gyrX, &calData.gyrY, &calData.gyrZ);
    accX += calData.accX; accY += calData.accY; accZ += calData.accZ;
    gyrX += calData.gyrX; gyrY += calData.gyrY; gyrZ += calData.gyrZ;
  }
  offsets[sensorId].accX = (int16_t)(accX / 100);
  offsets[sensorId].accY = (int16_t)(accY / 100);
  offsets[sensorId].accZ = (int16_t)(accZ / 100);
  offsets[sensorId].gyrX = (int16_t)(gyrX / 100);
  offsets[sensorId].gyrY = (int16_t)(gyrY / 100);
  offsets[sensorId].gyrZ = (int16_t)(gyrZ / 100);
  Serial.print("Sensor "); Serial.print(sensorId); Serial.println(" calibrated.");
}

void setMPU6050scales(uint8_t Gyro, uint8_t Accl) {
  sensor.setFullScaleGyroRange(Gyro);
  sensor.setFullScaleAccelRange(Accl);  
}




























// #include <Arduino.h>
// #include <Wire.h>
// #include <MPU6050.h>
// #include <ESP8266WiFi.h>

// #include <PubSubClient.h>

// // Configurações do Wi-Fi
// const char* ssid = "Gabriel Mendes";
// const char* password = "mendes123@*";

// // Configurações do MQTT
// const char* mqtt_broker = "192.168.75.69";  // Substitua pelo IP correto do seu notebook
// const int mqtt_port = 1883;
// const char* mqtt_topic = "sensor/mpu6050";
// int failedPublishes = 0;

// unsigned long lastTime = 0;
// unsigned long interval = 100;  // Intervalo de 100 ms
// unsigned long publishCount = 0;  // Contagem de mensagens publicadas

// // Configurações dos sensores
// #define MPUADDR 0x68
// #define TCAADDR 0x70
// #define SENSOR_RANGE_START 2
// #define SENSOR_RANGE_END 6
// #define BAUDRATE 460800

// const uint8_t portArray[] = {16, 5, 4, 0, 2, 14, 12, 13};
// const String dPortMap[] = {"D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"};

// struct sensorData {
//   int16_t accX, accY, accZ;
//   int16_t gyrX, gyrY, gyrZ;
// };

// // Globais
// uint8_t sdaPort, sclPort;
// MPU6050 sensor(MPUADDR);
// sensorData offsets[8];
// WiFiClient espClient;
// PubSubClient client(espClient);

// // Funções
// bool findConnection();
// void multiplexer_select(uint8_t i);
// void calibrate_sensor(uint8_t i);
// void setMPU6050scales(uint8_t Gyro, uint8_t Accl);
// void setup_wifi();
// void reconnect();

// void setup() {
//   Serial.begin(BAUDRATE);
//   Serial.println("\n\nGesture framework glove starting up.");

//   setup_wifi();
//   client.setServer(mqtt_broker, mqtt_port);

//   while (!findConnection()) {}
//   Serial.print("Connection to multiplexer found on SDA:");
//   Serial.print(dPortMap[sdaPort]);
//   Serial.print(" SCL:");
//   Serial.println(dPortMap[sclPort]);

//   for (uint8_t i = SENSOR_RANGE_START; i <= SENSOR_RANGE_END; i++) {
//     multiplexer_select(i);
//     Serial.print("Sensor "); Serial.print(i); Serial.print(": MPU6050 connection ");
//     sensor.initialize();
//     setMPU6050scales(MPU6050_GYRO_FS_1000, MPU6050_ACCEL_FS_4);
//     Serial.println(sensor.testConnection() ? "successful" : "failed");
//     calibrate_sensor(i);
//   }
//   Serial.println("Setup complete.");
//   delay(2500);

//   lastTime = millis();  // Inicializa o tempo
// }

// void loop() {
//   if (!client.connected()) {
//     reconnect();
//   }
//   client.loop();

//   unsigned long startLoopTime = millis();  

//     sensorData data;
//     String json = "{";
  
//     for (uint8_t i = SENSOR_RANGE_START; i <= SENSOR_RANGE_END; i++) {
//       multiplexer_select(i);
//       sensor.getMotion6(&data.accX, &data.accY, &data.accZ, &data.gyrX, &data.gyrY, &data.gyrZ);

//       data.accX -= offsets[i].accX;
//       data.accY -= offsets[i].accY;
//       data.accZ -= offsets[i].accZ;
//       data.gyrX -= offsets[i].gyrX;
//       data.gyrY -= offsets[i].gyrY;
//       data.gyrZ -= offsets[i].gyrZ;

//       json += "\"" + String(i) + "\":[";
//       json += String(data.accX) + ",";
//       json += String(data.accY) + ",";
//       json += String(data.accZ) + ",";
//       json += String(data.gyrX) + ",";
//       json += String(data.gyrY) + ",";
//       json += String(data.gyrZ);
//       json += "],";
//     }
//     json.remove(json.length() - 1);  // Remove a última vírgula
//     json += "}";

//     // Serial.print("Tamanho do JSON: ");
//     // Serial.println(json.length());
//     // Serial.println("Tentando publicar: " + json);
//     bool publishSuccess = client.publish(mqtt_topic, json.c_str());
//     publishCount++;  // Incrementa a contagem de publicações bem-sucedidas

//     if (publishSuccess) {
//       // Serial.println("Publicação bem-sucedida");
//       failedPublishes = 0;
//     } else {
//       failedPublishes++;
//       Serial.println("Falha na publicação MQTT. Tentativa: " + String(failedPublishes));
//     }

//   delay(5);

//   unsigned long currentMillis = millis();  // Obtém o tempo atual
//   Serial.print("Tempo de execução de um loop:");
//   Serial.println(currentMillis - startLoopTime);

//   // if (currentMillis - lastTime >= interval) {
//   //   // Passou o intervalo de 100ms, calcule e envie os dados
//   //   // Calcula a taxa de publicações
//   //   Serial.print("Taxa de publicação: ");
//   //   Serial.print(publishCount);  // Taxa em publicações por segundo
//   //   Serial.println(" publicações/100 milisegundos");

//   //   // Atualiza o tempo e reseta o contador
//   //   lastTime = currentMillis;
//   //   publishCount = 0;
//   // }
// }

// // void loop() {
// //   if (!client.connected()) {
// //     reconnect();
// //   }
// //   client.loop();

// //   sensorData data;
// //   String json = "{";
  
// //   for (uint8_t i = SENSOR_RANGE_START; i <= SENSOR_RANGE_END; i++) {
// //     multiplexer_select(i);
// //     sensor.getMotion6(&data.accX, &data.accY, &data.accZ, &data.gyrX, &data.gyrY, &data.gyrZ);

// //     data.accX -= offsets[i].accX;
// //     data.accY -= offsets[i].accY;
// //     data.accZ -= offsets[i].accZ;
// //     data.gyrX -= offsets[i].gyrX;
// //     data.gyrY -= offsets[i].gyrY;
// //     data.gyrZ -= offsets[i].gyrZ;

// //     json += "\"" + String(i) + "\":[";
// //     json += String(data.accX) + ",";
// //     json += String(data.accY) + ",";
// //     json += String(data.accZ) + ",";
// //     json += String(data.gyrX) + ",";
// //     json += String(data.gyrY) + ",";
// //     json += String(data.gyrZ);
// //     json += "],";
// //   }
// //   json.remove(json.length() - 1);  // Remove a última vírgula
// //   json += "}";

// //   bool publishSuccess = client.publish(mqtt_topic, json.c_str());

// //   if (publishSuccess) {
// //     Serial.println("Publicação bem-sucedida");
// //     failedPublishes = 0;
// //   } else {
// //     failedPublishes++;
// //     Serial.println("Falha na publicação MQTT. Tentativa: " + String(failedPublishes));
// //   }
  
// //   delay(5);  // Ajuste conforme necessário para controlar a taxa de envio
// // }

// void setup_wifi() {
//   delay(10);
//   Serial.println("Conectando ao WiFi");
//   WiFi.begin(ssid, password);
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
//   Serial.println("");
//   Serial.println("WiFi conectado");
//   Serial.print("Endereço IP: ");
//   Serial.println(WiFi.localIP());
// }

// void reconnect() {
//   while (!client.connected()) {
//     Serial.print("Tentando conexão MQTT...");
//     String clientId = "ESP8266Client-";
//     clientId += String(random(0xffff), HEX);
//     if (client.connect(clientId.c_str())) {
//       Serial.println("conectado");
//     } else {
//       Serial.print("falhou, rc=");
//       Serial.print(client.state());
//       Serial.println(" tentando novamente em 5 segundos");
//       delay(5000);
//     }
//   }
// }

// bool findConnection() {
//   for (uint8_t i = 0; i < sizeof(portArray); i++) {
//     for (uint8_t j = 0; j < sizeof(portArray); j++) {
//       if (i != j) {
//         Wire.begin(portArray[i], portArray[j]);
//         Wire.beginTransmission(TCAADDR);
//         byte error = Wire.endTransmission();
//         if (!error) {
//           sdaPort = i;
//           sclPort = j;
//           return true;
//         }
//       }
//     }
//   }
//   return false;
// }

// void multiplexer_select(uint8_t i) {
//   if (i > 7) return;
//   Wire.beginTransmission(TCAADDR);
//   Wire.write(1 << i);
//   Wire.endTransmission();
// }

// void calibrate_sensor(uint8_t sensorId) {
//   multiplexer_select(sensorId);
//   sensorData calData;
//   int32_t accX = 0, accY = 0, accZ = 0, gyrX = 0, gyrY = 0, gyrZ = 0;

//   for (uint8_t i = 0; i < 100; i++) {    
//     sensor.getMotion6(&calData.accX, &calData.accY, &calData.accZ, &calData.gyrX, &calData.gyrY, &calData.gyrZ);
//     accX += calData.accX; accY += calData.accY; accZ += calData.accZ;
//     gyrX += calData.gyrX; gyrY += calData.gyrY; gyrZ += calData.gyrZ;
//   }
//   offsets[sensorId].accX = (int16_t)(accX / 100);
//   offsets[sensorId].accY = (int16_t)(accY / 100);
//   offsets[sensorId].accZ = (int16_t)(accZ / 100);
//   offsets[sensorId].gyrX = (int16_t)(gyrX / 100);
//   offsets[sensorId].gyrY = (int16_t)(gyrY / 100);
//   offsets[sensorId].gyrZ = (int16_t)(gyrZ / 100);
//   Serial.print("Sensor "); Serial.print(sensorId); Serial.println(" calibrated.");
// }

// void setMPU6050scales(uint8_t Gyro, uint8_t Accl) {
//   sensor.setFullScaleGyroRange(Gyro);
//   sensor.setFullScaleAccelRange(Accl);  
// }