/*
 * SmartWater IoT – ESP32 + capteur ultrason (HC-SR04 ou JSN-SR04T étanche)
 *
 * Mesure la distance jusqu'à la surface de l'eau et l'envoie au serveur Django :
 *   - MODE_HTTP : POST https://<votre-domaine>/api/mesures/  (en-tête X-API-Key)
 *                 ou http://<IP du PC>:8000/api/mesures/ en local
 *   - MODE_MQTT : publie sur smartwater/capteurs/<ID_CAPTEUR>/mesure
 * Le serveur calcule le niveau : (hauteur_cm - distance_cm) / hauteur_cm * 100.
 *
 * Câblage (ESP32 DevKit) :
 *   VCC capteur -> 5V (VIN)     GND -> GND
 *   TRIG        -> GPIO 5
 *   ECHO        -> GPIO 18 via un pont diviseur (1 kΩ / 2 kΩ) : l'ECHO sort du 5 V,
 *                  l'ESP32 n'accepte que 3,3 V !
 *
 * Bibliothèques (Arduino IDE > Gérer les bibliothèques) : ArduinoJson ; PubSubClient (si MQTT)
 * Carte : « ESP32 Dev Module » (paquet esp32 by Espressif)
 */
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---------- À MODIFIER ----------
const char* WIFI_SSID     = "MonWiFi";
const char* WIFI_PASSWORD = "MotDePasseWiFi";
// Serveur en ligne (Docker + domaine) :  "https://smartwater.mondomaine.com/api/mesures/"
// Serveur local (runserver 0.0.0.0:8000) : "http://192.168.1.20:8000/api/mesures/"
const char* API_URL       = "https://smartwater.mondomaine.com/api/mesures/";
const char* API_KEY       = "COLLER_ICI_LA_CLE_DU_CAPTEUR";            // Réservoirs > Modifier > Clé d'API
const int   ID_CAPTEUR    = 1;

#define MODE_HTTP          // commentez cette ligne et décommentez la suivante pour utiliser MQTT
// #define MODE_MQTT
const char* MQTT_HOST = "smartwater.mondomaine.com";   // votre domaine (Docker) ou l'IP du PC en local
const int   MQTT_PORT = 1883;
const char* MQTT_USER = "esp32";                       // MQTT_USER du fichier .env du serveur
const char* MQTT_PASS = "MOT_DE_PASSE_MQTT";           // MQTT_PASSWORD du fichier .env du serveur
// --------------------------------

const int PIN_TRIG = 5;
const int PIN_ECHO = 18;
unsigned long intervalleMs = 10000;   // mis à jour par la réponse du serveur (Paramètres > Appareil)

#ifdef MODE_MQTT
#include <PubSubClient.h>
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
#endif

float mesurerDistanceCm() {
  // médiane de 5 mesures pour éliminer les valeurs aberrantes (vagues, échos)
  float v[5];
  for (int i = 0; i < 5; i++) {
    digitalWrite(PIN_TRIG, LOW);  delayMicroseconds(2);
    digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);
    unsigned long duree = pulseIn(PIN_ECHO, HIGH, 30000);   // 30 ms max ≈ 5 m
    v[i] = duree ? duree * 0.0343f / 2.0f : -1;
    delay(60);
  }
  for (int i = 0; i < 4; i++) for (int j = i + 1; j < 5; j++) if (v[j] < v[i]) { float t = v[i]; v[i] = v[j]; v[j] = t; }
  return v[2];
}

void connecterWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connexion au WiFi %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) { delay(500); Serial.print("."); }
  Serial.println(WiFi.status() == WL_CONNECTED ? " OK " + WiFi.localIP().toString() : " échec");
}

#ifdef MODE_HTTP
void envoyer(float distance) {
  HTTPClient http;
  WiFiClientSecure clientTLS;
  WiFiClient clientSimple;
  if (String(API_URL).startsWith("https")) {
    // Chiffrement HTTPS sans vérification du certificat (simple pour un projet étudiant).
    // Pour plus de sécurité : clientTLS.setCACert(<certificat racine ISRG Root X1 de Let's Encrypt>).
    clientTLS.setInsecure();
    http.begin(clientTLS, API_URL);
  } else {
    http.begin(clientSimple, API_URL);
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  String corps = String("{\"distance_cm\":") + String(distance, 1) + "}";
  int code = http.POST(corps);
  String rep = http.getString();
  Serial.printf("HTTP %d : %s\n", code, rep.c_str());
  if (code == 201) {
    JsonDocument doc;
    if (!deserializeJson(doc, rep) && doc["frequence_envoi_s"]) intervalleMs = doc["frequence_envoi_s"].as<unsigned long>() * 1000UL;
  }
  http.end();
}
#endif

#ifdef MODE_MQTT
void envoyer(float distance) {
  if (!mqtt.connected()) {
    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    String id = "esp32-smartwater-" + String(ID_CAPTEUR);
    if (!mqtt.connect(id.c_str(), MQTT_USER, MQTT_PASS)) { Serial.println("MQTT : connexion impossible"); return; }
  }
  char topic[64];
  snprintf(topic, sizeof topic, "smartwater/capteurs/%d/mesure", ID_CAPTEUR);
  String msg = String("{\"cle\":\"") + API_KEY + "\",\"distance_cm\":" + String(distance, 1) + "}";
  Serial.printf("MQTT %s -> %s : %s\n", topic, msg.c_str(), mqtt.publish(topic, msg.c_str()) ? "OK" : "échec");
  mqtt.loop();
}
#endif

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  connecterWifi();
}

void loop() {
  connecterWifi();
  float d = mesurerDistanceCm();
  if (d > 0) {
    Serial.printf("Distance : %.1f cm\n", d);
    if (WiFi.status() == WL_CONNECTED) envoyer(d);
  } else {
    Serial.println("Aucun écho : vérifiez le câblage du capteur");
  }
  delay(intervalleMs);
}
