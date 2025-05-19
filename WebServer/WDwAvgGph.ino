// WSmDNSGraph


#include <WiFi.h>
#include <time.h>
#include <WebServer.h>
#include "secrets.h"
#include <DNSServer.h>
#include <ESPmDNS.h>
#include <Ticker.h>

#define LORA_RX 17
#define LORA_TX 16

String loraBuffer = "";
int lastRSSI = -100;

#define MAX_RECORDS 60  // assuming ~1 data point every 30 seconds

struct WeatherData {
  int aqi;
  float temperature;
  float humidity;
  int pressure;
  int altitude;
  float light;
  float lightperc;
  String timestamp;
  time_t epoch;
  int rssi;
};

String latestData = "";
float latestTemp = 0.0;

const int maxDataPoints = 20;
float temperatureData[maxDataPoints];
int tempIndex = 0;

String getContentType(String filename) {
  if (filename.endsWith(".htm") || filename.endsWith(".html")) return "text/html";
  else if (filename.endsWith(".css")) return "text/css";
  else if (filename.endsWith(".js")) return "application/javascript";
  return "text/plain";
}

WeatherData dataBuffer[MAX_RECORDS];
int bufferSize = 0;
WebServer server(80);
bool isCaptivePortal = false;

DNSServer dnsServer;
const byte DNS_PORT = 53;
const char* localHostname = "loraweather";



String getLocalTimeString() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return "TIME ERROR";
  }
  char timeStr[20];
  strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", &timeinfo);
  return String(timeStr);
}

void readLoRaData() {
  while (Serial1.available()) {
    char c = Serial1.read();
    if (c == '\n') {
      loraBuffer.trim();
      if (loraBuffer.length() > 0) {
        parseLoRaMessage(loraBuffer);
      }
      loraBuffer = "";
    } else {
      loraBuffer += c;
    }
  }
}

void parseLoRaMessage(String message) {
  if (message.startsWith("+RCV=")) {
    message = message.substring(5);
    int comma1 = message.indexOf(',');
    int comma2 = message.indexOf(',', comma1 + 1);
    int comma3 = message.indexOf(',', comma2 + 1);
    int comma4 = message.indexOf(',', comma3 + 1);

    String sender = message.substring(0, comma1);
    String length = message.substring(comma1 + 1, comma2);
    String payload = message.substring(comma2 + 1, comma3);
    String SNR = message.substring(comma3 + 1, comma4);
    String RSSI = message.substring(comma4 + 1);

    lastRSSI = RSSI.toInt();
    
    Serial.println("=== LoRa Message Received ===");
    Serial.println("From: " + sender);
    Serial.println("Length: " + length);
    Serial.println("Payload: " + payload);
    Serial.println("SNR: " + SNR);
    Serial.println("RSSI: " + RSSI);
    Serial.println("==============================");

    if (payload.startsWith("AQI:")) {
      String timestamp = getLocalTimeString();
      WeatherData w = parseWeatherString(payload, timestamp);
      w.rssi = RSSI.toInt(); 

      struct tm timeinfo;
      getLocalTime(&timeinfo);
      w.epoch = mktime(&timeinfo);

      temperatureData[tempIndex] = w.temperature;
      tempIndex = (tempIndex + 1) % maxDataPoints;

      if (bufferSize < MAX_RECORDS) {
        dataBuffer[bufferSize++] = w;
      } else {
        for (int i = 1; i < MAX_RECORDS; i++) {
          dataBuffer[i - 1] = dataBuffer[i];
        }
        dataBuffer[MAX_RECORDS - 1] = w;
      }

      Serial.println("---- Weather Data ----");
      Serial.println("Time: " + w.timestamp);
      Serial.print("AQI: "); Serial.println(w.aqi);
      Serial.print("Temp: "); Serial.println(w.temperature);
      Serial.print("Humidity: "); Serial.println(w.humidity);
      Serial.print("Pressure: "); Serial.println(w.pressure);
      Serial.print("Altitude: "); Serial.println(w.altitude);
      Serial.print("Light Level: "); Serial.println(w.light);

      printHourlyAverages();
    }
  } else {
    Serial.println("Other LoRa Response: " + message);
  }
}

WeatherData parseWeatherString(String input, String timestamp) {
  WeatherData data;
  input.trim();
  data.timestamp = timestamp;

  int start = 0;
  while (start < input.length()) {
    int sep = input.indexOf(':', start);
    int end = input.indexOf(';', sep);
    if (end == -1) end = input.length();

    String key = input.substring(start, sep);
    String value = input.substring(sep + 1, end);

    if (key == "AQI") data.aqi = value.toInt();
    else if (key == "T") data.temperature = value.toFloat();
    else if (key == "RH") data.humidity = value.toFloat();
    else if (key == "hPa") data.pressure = value.toInt();
    else if (key == "Alt") data.altitude = value.toInt();
    else if (key == "L") data.light = value.toFloat();

    data.lightperc = data.light * 30.77;
    start = end + 1;
  }
  
  return data;
}

String getAveragesHTML() {
  time_t now;
  struct tm timeinfo;
  getLocalTime(&timeinfo);
  now = mktime(&timeinfo);

  float sumAQI = 0, sumTemp = 0, sumHum = 0, sumPress = 0, sumAlt = 0, sumLight = 0, sumLightperc = 0;
  int count = 0;

  for (int i = 0; i < bufferSize; i++) {
    if (difftime(now, dataBuffer[i].epoch) <= 3600) {
      sumAQI += dataBuffer[i].aqi;
      sumTemp += dataBuffer[i].temperature;
      sumHum += dataBuffer[i].humidity;
      sumPress += dataBuffer[i].pressure;
      sumAlt += dataBuffer[i].altitude;
      sumLight += dataBuffer[i].light;
      sumLightperc += dataBuffer[i].lightperc;
      count++;
    }
  }

  if (count == 0) return "<p>No recent data to average.</p>";

  String html = "<table><tr><th>Metric</th><th>Average</th></tr>";
  html += "<tr><td>AQI</td><td>" + String(sumAQI / count, 1) + "</td></tr>";
  html += "<tr><td>Temperature (°C)</td><td>" + String(sumTemp / count, 1) + "</td></tr>";
  html += "<tr><td>Humidity (%)</td><td>" + String(sumHum / count, 1) + "</td></tr>";
  html += "<tr><td>Pressure (hPa)</td><td>" + String(sumPress / count, 1) + "</td></tr>";
  html += "<tr><td>Altitude (m)</td><td>" + String(sumAlt / count, 1) + "</td></tr>";
  html += "<tr><td>Light (V)</td><td>" + String(sumLight / count, 2) + "</td></tr>";
  html += "<tr><td>Light (%)</td><td>" + String(sumLightperc / count, 1) + "</td></tr>";
  html += "</table>";

  return html;
}

void printHourlyAverages() {
  time_t now;
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    now = mktime(&timeinfo);
  } else {
    Serial.println("Failed to get time");
    return;
  }

  float sumAQI = 0, sumTemp = 0, sumHum = 0, sumPress = 0, sumAlt = 0, sumLight = 0, sumLightperc = 0;
  int count = 0;

  for (int i = 0; i < bufferSize; i++) {
    if (difftime(now, dataBuffer[i].epoch) <= 3600) {
      sumAQI += dataBuffer[i].aqi;
      sumTemp += dataBuffer[i].temperature;
      sumHum += dataBuffer[i].humidity;
      sumPress += dataBuffer[i].pressure;
      sumAlt += dataBuffer[i].altitude;
      sumLight += dataBuffer[i].light;
      sumLightperc += dataBuffer[i].lightperc;
      count++;
    }
  }

  if (count == 0) {
    Serial.println("No recent data to average.");
    return;
  }

  Serial.println("---- Hourly Averages ----");
  Serial.printf("Avg AQI: %.1f\n", sumAQI / count);
  Serial.printf("Avg Temp (°C): %.1f\n", sumTemp / count);
  Serial.printf("Avg RH (%%): %.1f\n", sumHum / count);
  Serial.printf("Avg Pressure (hPa): %.1f\n", sumPress / count);
  Serial.printf("Avg Altitude (m): %.1f\n", sumAlt / count);
  Serial.printf("Avg Light (V): %.2f\n", sumLight / count);
  Serial.printf("Avg Light (%): %.1f\n", sumLightperc / count);
}

String getSignalStrengthBar(int rssi) {
  int percentage = constrain(map(rssi, -100, -40, 0, 100), 0, 100);
  String color = (rssi > -70) ? "green" : (rssi > -90) ? "orange" : "red";
  String html = "<div style='border:1px solid #ccc;width:100%;height:20px;'><div style='height:100%;width:" + String(percentage) + "%;background-color:" + color + "'></div></div>";
  return html;
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><meta charset='UTF-8'>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<title>Weather Dashboard</title>";
  html += "<style>body{font-family:sans-serif;padding:2em;}table{border-collapse:collapse;}td,th{padding:0.5em;border:1px solid #ccc;}</style>";
  html += "</head><body>";
  html += "<h1>Latest Weather Data</h1>";

  if (bufferSize > 0) {
    WeatherData latest = dataBuffer[bufferSize - 1];
    html += "<table><tr><th>Metric</th><th>Value</th></tr>";
    html += "<tr><td>AQI</td><td>" + String(latest.aqi) + "</td></tr>";
    html += "<tr><td>Temperature (°C)</td><td>" + String(latest.temperature) + "</td></tr>";
    html += "<tr><td>Humidity (%)</td><td>" + String(latest.humidity) + "</td></tr>";
    html += "<tr><td>Pressure (hPa)</td><td>" + String(latest.pressure) + "</td></tr>";
    html += "<tr><td>Altitude (m)</td><td>" + String(latest.altitude) + "</td></tr>";
    html += "<tr><td>Light (V)</td><td>" + String(latest.light) + "</td></tr>";
    html += "<tr><td>Light (%)</td><td>" + String(latest.lightperc) + "</td></tr>"; 
    html += "<tr><td>LoRa RSSI (dBm)</td><td>" + String(latest.rssi) + "</td></tr>";
    html += "<tr><td>Timestamp</td><td>" + latest.timestamp + "</td></tr>";
    html += "</table>";
  } else {
    html += "<p>No data available.</p>";
  }

  html += "<h2>LoRa Signal Strength</h2>";
  html += "<p>RSSI: " + String(lastRSSI) + " dBm</p>";
  html += getSignalStrengthBar(lastRSSI);
  html += "<p><small><strong>-70 dBm or higher:</strong> Excellent | <strong>-90 dBm to -70 dBm:</strong> Okay | <strong>-100 dBm to -90 dBm:</strong> Weak</small></p>";

  html += "<h2>Hourly Averages</h2>";
  html += getAveragesHTML();
  html += "<p><em>Page refreshes every 60 seconds</em></p>";
  html += "<script>setTimeout(()=>location.reload(),60000);</script>";
  html += "</body></html>";

  String graphs = R"rawliteral(
      <title>Weather Dashboard</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body { font-family: sans-serif; text-align: center; margin: 20px; }
        canvas { max-width: 600px; margin: auto; }
      </style>
    </head>
    <body>
      <h1>LoRa Weather Dashboard</h1>
      <div id="dataDisplay">Loading latest data...</div>
      <canvas id="tempChart" width="600" height="300"></canvas>

      <script>
        let tempChart;

        async function fetchData() {
          const res = await fetch('/data');
          const json = await res.json();

          document.getElementById('dataDisplay').innerText = json.latest;

          if (!tempChart) {
            const ctx = document.getElementById('tempChart').getContext('2d');
            tempChart = new Chart(ctx, {
              type: 'line',
              data: {
                labels: json.history.map((_, i) => i + 1),
                datasets: [{
                  label: 'Temperature (°C)',
                  data: json.history,
                  borderColor: 'orange',
                  fill: false
                }]
              },
              options: {
                responsive: true,
                scales: {
                  y: { beginAtZero: true }
                }
              }
            });
          } else {
            tempChart.data.labels = json.history.map((_, i) => i + 1);
            tempChart.data.datasets[0].data = json.history;
            tempChart.update();
          }
        }

        setInterval(fetchData, 2000);
        fetchData();
      </script>
    </body>
    </html>
  )rawliteral";
  html += graphs;
  server.send(200, "text/html", html);
}

void handleDataJson() {
  String json = "{";
  json += "\"latest\":\"" + latestData + "\",";
  json += "\"history\":[";
  for (int i = 0; i < maxDataPoints; i++) {
    if (i > 0) json += ",";
    json += String(temperatureData[(tempIndex + i) % maxDataPoints]);
  }
  json += "]}";
  server.send(200, "application/json", json);
}



void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, LORA_RX, LORA_TX);
  Serial.println("LoRa Parser Ready");

  // Before WiFi.begin()
  WiFi.mode(WIFI_AP_STA);  // allow AP and STA mode together
  WiFi.setHostname(localHostname);  // for mDNS when connected to other networks

  // Start WiFi AP
  WiFi.softAP("WeatherNode", "weather123");

  // Start DNS redirect for captive portal
  dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());


  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 10000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi!");
    Serial.print("Web server IP address: ");
    Serial.println(WiFi.localIP());
    if (MDNS.begin(localHostname)) {
      Serial.println("mDNS responder started");
      Serial.print("You can access via http://");
      Serial.print(localHostname);
      Serial.println(".local");
    } else {
      Serial.println("Error setting up MDNS");
    }
    isCaptivePortal = false;
  } else {
    Serial.println("\nWiFi failed. Starting Access Point...");
    isCaptivePortal = true;
    WiFi.softAP("WeatherNode", "weather1234");
    IPAddress AP_IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(AP_IP);
  }

  configTzTime("PST8PDT,M3.2.0,M11.1.0", "pool.ntp.org");

  server.on("/", handleRoot);
  server.on("/data", handleDataJson);
  server.begin();
  Serial.println("Web server started.");

  server.onNotFound([]() {
    server.sendHeader("Location", "/", true);
    server.send(302, "text/plain", "");
  });
}

void loop() {
  readLoRaData();

  server.handleClient();
  dnsServer.processNextRequest();
  if (Serial.available()) {
    Serial1.write(Serial.read());
  }
}