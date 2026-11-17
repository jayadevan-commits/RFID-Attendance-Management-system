
#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

// RFID pins - unchanged
#define SS_PIN   5
#define RST_PIN  10

#define SCK_PIN  12
#define MISO_PIN 13
#define MOSI_PIN 11

MFRC522 rfid(SS_PIN, RST_PIN);

// WiFi credentials
//Basha
// const char* WIFI_SSID = "Mushraf's A34";
// const char* WIFI_PASSWORD = "11111111";
//vasanth
const char* WIFI_SSID = "vivo T3x 5G";
const char* WIFI_PASSWORD = "10000000";


// MQTT broker
const char* MQTT_BROKER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

const char* MQTT_TOPIC =
    "jayadevan_attendance/device01/card_scan";

const char* DEVICE_ID = "ESP32_ATTENDANCE_01";

// MQTT objects
WiFiClient espClient;
PubSubClient mqtt(espClient);


// Connect ESP32 to WiFi
void connectWiFi() {
  WiFi.disconnect(true);
  delay(500);
  WiFi.mode(WIFI_STA);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
      delay(500);
      Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
      Serial.print("\nFailed, status code: ");
      Serial.println(WiFi.status());
      WiFi.disconnect(true);
      delay(2000);   // wait, then try again
    }
  }

  Serial.println();
  Serial.println("WiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}


// Connect ESP32 to MQTT
void connectMQTT() {

  while (!mqtt.connected()) {

    Serial.print("Connecting to MQTT...");

    if (mqtt.connect("RFID_ESP32_ATTENDANCE_01")) {

      Serial.println("Connected!");

    } else {

      Serial.print("Failed, state: ");
      Serial.println(mqtt.state());

      delay(2000);
    }
  }
}


// Convert RFID UID and publish JSON
void publishRFID() {

  char uid[32] = "";

  for (byte i = 0; i < rfid.uid.size; i++) {

    char part[4];

    sprintf(part, "%02X", rfid.uid.uidByte[i]);

    strcat(uid, part);

    if (i < rfid.uid.size - 1) {
      strcat(uid, " ");
    }
  }

  char payload[200];

  snprintf(
    payload,
    sizeof(payload),
    "{\"device_id\":\"%s\",\"uid\":\"%s\",\"event\":\"CARD_SCANNED\"}",
    DEVICE_ID,
    uid
  );

  Serial.print("Card UID: ");
  Serial.println(uid);

  if (mqtt.publish(MQTT_TOPIC, payload, false)) {

    Serial.println("MQTT Message Published!");

  } else {

    Serial.println("MQTT Publish Failed!");
  }
}


void setup() {

  Serial.begin(115200);
  delay(2000);

  Serial.println("ESP32-S3 Starting...");

  // Initialize RFID
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN);

  Serial.println("SPI Started");

  rfid.PCD_Init();
  delay(100);

  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);

  Serial.print("Firmware Version: 0x");
  Serial.println(version, HEX);

  Serial.println("RFID Reader Ready!");

  // Initialize WiFi
  connectWiFi();

  // Initialize MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);

  connectMQTT();

  Serial.println("Scan your card...");
}


void loop() {

  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Maintain MQTT connection
  if (!mqtt.connected()) {
    connectMQTT();
  }

  mqtt.loop();

  // Existing RFID reading logic
  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  if (!rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Publish UID to MQTT
  publishRFID();

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(500);
}
