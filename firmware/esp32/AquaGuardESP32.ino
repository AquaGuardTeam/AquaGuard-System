/* AquaGuard ESP32 firmware scaffold.
 * Confirm board, sensor modules, ADC ranges, touchscreen, relay/driver, and valve datasheets
 * before energizing hardware. GPIO26 is control-only; never connect a 12 V load directly.
 */
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "hardware_config.h"

constexpr int PH_PIN = AQUAGUARD_PH_PIN;
constexpr int TDS_PIN = AQUAGUARD_TDS_PIN;
constexpr int TURBIDITY_PIN = AQUAGUARD_TURBIDITY_PIN;
constexpr int VALVE_CONTROL_PIN = AQUAGUARD_VALVE_CONTROL_PIN;

const char* WIFI_SSID = AQUAGUARD_WIFI_SSID;
const char* WIFI_PASSWORD = AQUAGUARD_WIFI_PASSWORD;
const char* API_URL = AQUAGUARD_API_HOST "/api/readings";
const char* DEVICE_TOKEN = AQUAGUARD_DEVICE_TOKEN;
const unsigned long SAMPLE_INTERVAL_MS = AQUAGUARD_SAMPLE_INTERVAL_MS;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  pinMode(VALVE_CONTROL_PIN, OUTPUT);
  digitalWrite(VALVE_CONTROL_PIN, LOW);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(250);
  }
  if (WiFi.status() == WL_CONNECTED) {
    configTime(8 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  }
}

float samplePHSensor() { return constrain(analogRead(PH_PIN) / 4095.0 * 14.0, 0.0, 14.0); }
float sampleTDSSensor() { return constrain(analogRead(TDS_PIN) / 4095.0 * 1000.0, 0.0, 1000.0); }
float sampleTurbiditySensor() { return constrain(analogRead(TURBIDITY_PIN) / 4095.0 * 100.0, 0.0, 100.0); }

void loop() {
  static unsigned long previousSample = 0;
  if (millis() - previousSample < SAMPLE_INTERVAL_MS) return;
  previousSample = millis();

  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    return;
  }

  StaticJsonDocument<256> payload;
  payload["timestamp"] = isoTimestamp();
  payload["ph"] = samplePHSensor();
  payload["tds_ppm"] = sampleTDSSensor();
  payload["turbidity_ntu"] = sampleTurbiditySensor();

  String body;
  serializeJson(payload, body);
  WiFiClientSecure secureClient;
  secureClient.setCACert(AQUAGUARD_CA_CERT);
  HTTPClient http;
  if (!String(API_URL).startsWith("https://")) {
    Serial.println("HTTPS required: set AQUAGUARD_API_HOST to an HTTPS URL");
    return;
  }
  if (strlen(AQUAGUARD_CA_CERT) == 0) {
    Serial.println("TLS CA certificate is not configured");
    return;
  }
  http.begin(secureClient, API_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
  int code = http.POST(body);

  if (code == 201) {
    StaticJsonDocument<256> response;
    deserializeJson(response, http.getString());
    if (response["condition"] == "Critical") {
      digitalWrite(VALVE_CONTROL_PIN, LOW); // fail-safe: close/stop water flow
    }
  }
  http.end();

  pollDispensingCommand();
}

void pollDispensingCommand() {
  if (!WiFi.isConnected() || strlen(AQUAGUARD_CA_CERT) == 0) return;
  WiFiClientSecure secureClient;
  secureClient.setCACert(AQUAGUARD_CA_CERT);
  HTTPClient http;
  http.begin(secureClient, String(API_URL).substring(0, String(API_URL).lastIndexOf('/')) + "/control/dispensing/latest");
  http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
  int code = http.GET();
  if (code == 200) {
    StaticJsonDocument<256> response;
    deserializeJson(response, http.getString());
    const char* command = response["command"];
    if (command && strcmp(command, "stop") == 0) {
      digitalWrite(VALVE_CONTROL_PIN, LOW);
    } else {
      const char* mode = response["mode"];
      if (mode && (strcmp(mode, "cold") == 0 || strcmp(mode, "room_temperature") == 0)) {
        digitalWrite(VALVE_CONTROL_PIN, HIGH);
      }
    }
  }
  http.end();
}

String isoTimestamp() {
  time_t now = time(nullptr);
  struct tm tm;
  gmtime_r(&now, &tm);
  char buffer[21];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &tm);
  return String(buffer);
}
