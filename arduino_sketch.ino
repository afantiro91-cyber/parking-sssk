/*
  Smart Parking System - Arduino Sketch
  Za ESP8266 ili Arduino sa WiFi modulom
  
  Komponente:
  - Arduino/ESP8266
  - Ultrasonic senzori (HC-SR04) - Jedan po mjestu
  - WiFi modul (za komunikaciju sa serverom)
  
  Pinove konfiguracija (prilagodi prema tebi):
  - Senzor 1: TRIGGER=5, ECHO=6
  - Senzor 2: TRIGGER=7, ECHO=8
  - Senzor 3: TRIGGER=9, ECHO=10
  - Senzor 4: TRIGGER=11, ECHO=12
  - Senzor 5: TRIGGER=13, ECHO=14
*/

// Za ESP8266
#ifdef ESP8266
  #include <ESP8266WiFi.h>
  #include <WiFiClient.h>
#endif

// Za Arduino sa WiFi Shield
#ifdef ARDUINO_AVR_LEONARDO
  #include <WiFi.h>
#endif

// Konstante
const char* SSID = "YOUR_WIFI_SSID";           // Unesi tvoj WiFi naziv
const char* PASSWORD = "YOUR_WIFI_PASSWORD";   // Unesi tvoju WiFi šifru
const char* SERVER = "192.168.1.100";          // IP adresa Python servera
const int PORT = 5000;                          // Port na kojem je Flask server

// Pin konfiguracija za ultrasonic senzore
struct ParkingSpot {
  int spotNumber;
  int triggerPin;
  int echoPin;
  int lastOccupancyState;
};

ParkingSpot spots[] = {
  {1, 5, 6, 0},
  {2, 7, 8, 0},
  {3, 9, 10, 0},
  {4, 11, 12, 0},
  {5, 13, 14, 0}
};

const int NUM_SPOTS = 5;
const int DISTANCE_THRESHOLD = 20; // cm - ako je manje, mjesto je zauzeto
const int CHECK_INTERVAL = 2000;   // ms - kako često čitati senzore

unsigned long lastCheckTime = 0;
WiFiClient client;

// Inicijalizacija
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("🚗 Smart Parking Arduino - Pokretanje...");
  
  // Inicijalizuj pin-ove za senzore
  for (int i = 0; i < NUM_SPOTS; i++) {
    pinMode(spots[i].triggerPin, OUTPUT);
    pinMode(spots[i].echoPin, INPUT);
    Serial.println("Pin konfiguracija: Senzor " + String(i + 1) + " OK");
  }
  
  // Povezivanje na WiFi
  connectToWiFi();
}

// Glavna petlja
void loop() {
  // Provjerite WiFi konekciju
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi veza prekinuta, pokušavam reconnect...");
    connectToWiFi();
    return;
  }
  
  // Provjerite senzore redovito
  unsigned long currentTime = millis();
  if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
    lastCheckTime = currentTime;
    checkAllSensors();
  }
  
  delay(100);
}

// Povezivanje na WiFi
void connectToWiFi() {
  Serial.print("🔗 Spajam se na WiFi: ");
  Serial.println(SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" ✅ Uspješno!");
    Serial.print("IP adresa: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" ❌ Greška!");
  }
}

// Provjera svih senzora
void checkAllSensors() {
  Serial.println("\n📡 Provjeravam sve senzore...");
  
  for (int i = 0; i < NUM_SPOTS; i++) {
    int distance = measureDistance(i);
    boolean occupied = (distance < DISTANCE_THRESHOLD);
    
    Serial.println("Senzor " + String(i + 1) + 
                   " - Distanca: " + String(distance) + 
                   " cm - Status: " + (occupied ? "🚫 ZAUZETO" : "✅ SLOBODNO"));
    
    // Ako se status promijenio, pošalji na server
    if (occupied != spots[i].lastOccupancyState) {
      spots[i].lastOccupancyState = occupied;
      sendToServer(i + 1, occupied);
    }
  }
}

// Čitanje rastojanja sa ultrasonic senzora
int measureDistance(int sensorIndex) {
  int triggerPin = spots[sensorIndex].triggerPin;
  int echoPin = spots[sensorIndex].echoPin;
  
  // Pošalji trigger impuls
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  
  // Čitaj echo impuls
  long duration = pulseIn(echoPin, HIGH, 30000);
  
  // Izračunaj rastojanje (brzina zvuka = 343 m/s)
  int distance = duration * 0.0343 / 2;
  
  return distance;
}

// Pošalji podatke na server
void sendToServer(int spotNumber, boolean occupied) {
  Serial.println("\n📤 Slanje na server...");
  
  if (!client.connect(SERVER, PORT)) {
    Serial.println("❌ Greška: Ne mogu se spojiti na server!");
    return;
  }
  
  // Pripremi podatke
  String status = occupied ? "OCCUPIED" : "FREE";
  String sensorData = "SPOT:" + String(spotNumber) + ":" + status;
  
  // Pošalji GET zahtjev (jednostavnije)
  String request = "GET /api/arduino?spot=" + String(spotNumber) + 
                   "&status=" + status + " HTTP/1.1\r\n";
  request += "Host: " + String(SERVER) + "\r\n";
  request += "Connection: close\r\n\r\n";
  
  client.print(request);
  
  // Čitaj odgovor
  while (client.connected()) {
    if (client.available()) {
      String response = client.readStringUntil('\n');
      Serial.println("📥 Odgovor: " + response);
    }
  }
  
  client.stop();
  Serial.println("✅ Podatak poslан");
}

/*
  NAPOMENE:
  
  1. Ultrasonic senzor HC-SR04:
     - Pošalje 10µs HIGH impuls na TRIGGER
     - Čeka ECHO pin da bude HIGH
     - Trajanje ECHO impulsa = 2 * rastojanje / brzina zvuka
  
  2. Distanca (cm) = duration (µs) * 0.0343 / 2
  
  3. WiFi konekcija:
     - Zamijeniti SSID i PASSWORD sa stvarima
     - Zamijeniti SERVER IP sa IP adresom tvog Python servera
  
  4. Pin konfiguracija:
     - Prilagoditi prema tvojoj konfiguraciji
     - Za ESP8266 koristi: D0=16, D1=5, D2=4, D3=0, D4=2, D5=14, D6=12, D7=13, D8=15
  
  5. Instalacija biblioteka:
     - Za ESP8266: Board Manager → esp8266 by ESP8266 Community
     - Za Arduino: Koristi ugrađene WiFi biblioteke
*/
