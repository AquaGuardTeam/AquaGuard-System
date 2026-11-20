#pragma once

// Replace these values for the installed unit. Never commit production Wi-Fi secrets.
#define AQUAGUARD_WIFI_SSID "CHANGE_ME"
#define AQUAGUARD_WIFI_PASSWORD "CHANGE_ME"
#define AQUAGUARD_API_HOST "https://aquaguard.example.local" // Use HTTPS in deployment
#define AQUAGUARD_CA_CERT "" // Paste the issuing CA PEM certificate here; do not deploy with this empty
#define AQUAGUARD_DEVICE_TOKEN "CHANGE_ME"

#define AQUAGUARD_PH_PIN 34
#define AQUAGUARD_TDS_PIN 35
#define AQUAGUARD_TURBIDITY_PIN 32
#define AQUAGUARD_VALVE_CONTROL_PIN 26

#define AQUAGUARD_SAMPLE_INTERVAL_MS 15000

// Calibrate against approved reference instruments before field use.
#define AQUAGUARD_PH_ZERO_ADCOUNTS 0
#define AQUAGUARD_PH_FULL_ADCOUNTS 4095
#define AQUAGUARD_TDS_ZERO_PPM 0.0
#define AQUAGUARD_TDS_FULL_PPM 1000.0
#define AQUAGUARD_TURBIDITY_ZERO_NTU 0.0
#define AQUAGUARD_TURBIDITY_FULL_NTU 100.0
