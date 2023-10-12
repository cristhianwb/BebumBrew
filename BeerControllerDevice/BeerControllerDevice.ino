#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Arduino_JSON.h>
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>

//Ac Controls Definitions

hw_timer_t * timer = NULL;
volatile uint32_t lastMicros;
volatile int triacDelay = 0;

const int ZERO_CROSS_PIN = 13;
const int DIMMER_PIN = 12;

uint8_t dim_enabled = LOW;

//Wifi and network definitions

const char* ssid = "Bankai";
const char* password = "macaquinho2015";

WebServer server(80);

const int led = 26;
const int pump_power_pin = 32;

int heater_power;
int pump_power;

double temp_sensor1 = 0;
double temp_sensor2 = 0;

const int level_sensor_pin = 27; 
bool level_sensor = false;

//Temp sensors

const int oneWireBus = 14;     

// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWire(oneWireBus);

// Pass our oneWire reference to Dallas Temperature sensor 
DallasTemperature sensors(&oneWire);

void IRAM_ATTR isr() {
  uint32_t Now=micros();
  if(Now-lastMicros>7000) { //10ms between zero crossings @50Hz, 7ms treshold to avoid false detections does the trick
    digitalWrite(DIMMER_PIN,LOW);     //stop pulse upon zero crossing
    lastMicros=Now;
    timerAlarmWrite(timer,triacDelay,true);
    timerAlarmEnable(timer);
    timerStart(timer);  
  }
}

void IRAM_ATTR onTimer(){
  digitalWrite(DIMMER_PIN, dim_enabled); //start pulse to ignite lamp after timer
  timerStop(timer);
}

bool set_heater_power(int power){
  if ((power>=0) && (power<=100)){
    triacDelay=(100-power) * 83;
    //Serial.print("Triac delay");
    //Serial.println(triacDelay);
    heater_power = power;
    dim_enabled = (power > 0) ? HIGH : LOW;
    return true;
  }
  return false;
}

bool set_pump_power(int power){
  if ((power>=0) && (power<=100)){
    ledcWrite(0, int((power / 100.0) * 1024.0));
    pump_power = power;
    return true;
  }
  return false;  
}

bool read_sensors(){
  temp_sensor1 = sensors.getTempCByIndex(0);
  temp_sensor2 = sensors.getTempCByIndex(1);
  sensors.requestTemperatures(); 
  level_sensor = !digitalRead(level_sensor_pin);
  return true;
}

void handleRoot() {
  JSONVar jsonObj;
  JSONVar jsonResponse;

  digitalWrite(led, 1);
  if (server.method() == HTTP_POST){
    jsonObj = JSON.parse(server.arg("plain"));
    if (JSON.typeof(jsonObj) != "undefined"){
      if ((JSON.typeof(jsonObj["heater_power"]) == "number") && set_heater_power(jsonObj["heater_power"])){
        Serial.print("Heater power changed to : ");
        Serial.println(heater_power);
      }
      
      if ((JSON.typeof(jsonObj["pump_power"]) == "number") && set_pump_power(jsonObj["pump_power"])){
        Serial.print("Pump power changed to : ");
        Serial.println(pump_power);
      }        
    }
  }

  jsonResponse["temp1"] = temp_sensor1;
  jsonResponse["temp2"] = temp_sensor2;
  jsonResponse["level"] = level_sensor;

  server.send(200, "text/plain", JSON.stringify(jsonResponse));
  digitalWrite(led, 0);
}

void handleNotFound() {
  //digitalWrite(led, 1);
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  server.send(404, "text/plain", message);
  //digitalWrite(led, 0);
}

void setup(void) {
  pinMode(led, OUTPUT);
  digitalWrite(led, 1);

  pinMode(pump_power_pin, OUTPUT);
  ledcAttachPin(pump_power_pin, 0);//Atribuimos o pino 2 ao canal 0.
  ledcSetup(0, 10000, 10);
  pinMode(level_sensor_pin, INPUT_PULLUP);
  
  Serial.begin(115200);

  //Ac Control Configurations
  pinMode(ZERO_CROSS_PIN, INPUT); //zero cross input
  pinMode(DIMMER_PIN, OUTPUT); // triac output
  attachInterrupt(ZERO_CROSS_PIN, isr, RISING);
  timer=timerBegin(0,80,true);  //although starting and stopping of the timer is done manually, it needs to be autoreload setting
  timerAttachInterrupt(timer,onTimer,true);

  //Temperature sensors configurations
  sensors.begin();

  //Network configurations
  WiFi.mode(WIFI_STA);
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  WiFi.begin(ssid, password);
  Serial.println("");

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  if (MDNS.begin("esp32")) {
    Serial.println("MDNS responder started");
  }

  //server.on("/setControls", handleSetControls);
  server.on("/", handleRoot);
  server.onNotFound(handleNotFound);

  server.begin();
  Serial.println("HTTP server started");
  digitalWrite(led, 0);
}

int last_millis = 0;

void loop(void) {
  if ((last_millis - millis()) >= 1000){
    read_sensors();
    last_millis = millis();
  }
  server.handleClient();
  delay(2);//allow the cpu to switch to other tasks
}
