#define MACADDRESS 0x00,0x01,0x02,0x03,0x04,0x05
#define MYIPADDR 192,168,1,6
#define MYIPMASK 255,255,255,0
#define MYDNS 192,168,1,1
#define MYGW 192,168,1,1
#define LISTENPORT 80
#define UARTBAUD 9600
#define ACTLOGLEVEL LOG_INFO

#include <UIPEthernet.h>
#include <Arduino_JSON.h>
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "Dimmer.h"

//Device Pin Out Definition
#define PUMP_MOSFET_PIN   13
#define ONE_WIRE_BUS_PIN  5
#define LEVEL_SENSOR_PIN  4
#define HEATER_TRIAC_PIN  3
//#define IND_LED_PIN       0
//#define DIMMER_ZERO_CROSS_PIN       2 (Defined in Dimmer.h)

typedef enum {GET, POST} METHOD;

//Variaveis globais dos sensores e atuadores
int heater_power;
int pump_power;
double temp_sensor1 = 0;
double temp_sensor2 = 0;
bool level_sensor = false;


//Sensor temperatura
OneWire oneWire(ONE_WIRE_BUS_PIN);
DallasTemperature sensors(&oneWire);
//Dimmer (ZC Pin 2)
Dimmer heater(HEATER_TRIAC_PIN);
//Servidor
EthernetServer server = EthernetServer(LISTENPORT);





bool set_heater_power(int power){
  if (((power>=0) && (power<=100)) && (power != heater_power)){
    heater_power = power;
    heater.set(heater_power);
    return true;
  }
  return false;
}

bool set_pump_power(int power){
  if (((power>=0) && (power<=100)) && (power != pump_power)){
    pump_power = power;
    analogWrite(PUMP_MOSFET_PIN, int((pump_power / 100.0) * 128.0));    
    return true;
  }
  return false;  
}

bool read_sensors(){
  temp_sensor1 = sensors.getTempCByIndex(0);
  temp_sensor2 = sensors.getTempCByIndex(1);
  sensors.requestTemperatures(); 
  level_sensor = !digitalRead(LEVEL_SENSOR_PIN);
  return true;
}

void respond(METHOD method, char* msg, EthernetClient client){
  char * response_cstr;
  JSONVar jsonObj;
  JSONVar jsonResponse;
  size_t res_size, json_size;
  
  #ifdef IND_LED_PIN
  digitalWrite(IND_LED_PIN, 1);
  #endif

  if (method == POST){
    jsonObj = JSON.parse(msg);
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
  const char* const response_format_str = "HTTP/1.1 200 OK"
                                          "Content-Type: text/html"
                                          "Content-Length: %d\r\n\r\n%s";

  String json_response_str = JSON.stringify(jsonResponse);
  json_size = json_response_str.length();
  res_size = strlen(response_format_str) +  + 10;
  char * response_str = (char*) malloc(res_size * sizeof(char));
  res_size = sprintf(response_str, response_format_str, json_size, json_response_str.c_str());
  client.write(response_str, res_size);
  free(response_str);
  
  #ifdef IND_LED_PIN
  digitalWrite(IND_LED_PIN, 1);
  #endif
}

void handle_requests(EthernetClient client){
  char *msg;
  size_t size;;
  METHOD method;

  size = client.available();
  
  if(size > 0){
    msg = (char*) calloc(size+1, sizeof(char*));
    size = client.read(msg, size);
    //find http version header
    if (strstr(msg, "HTTP/1.1") != NULL){
      if( strstr(msg, "POST") == msg)
        method = POST;
      else
        method = GET;

      respond(method, strstr(msg, "\r\n\r\n")+(4 * sizeof(char)), client); 
    } 
    
    //Serial.write(msg, size);
    //Serial.print("Size: ");
    //Serial.println(size);
    free(msg);
  }

   
}

void setup() {

  uint8_t mac[6] = {MACADDRESS};
  uint8_t myIP[4] = {MYIPADDR};
  uint8_t myMASK[4] = {MYIPMASK};
  uint8_t myDNS[4] = {MYDNS};
  uint8_t myGW[4] = {MYGW};
  
  pinMode(PUMP_MOSFET_PIN, OUTPUT);
  pinMode(LEVEL_SENSOR_PIN, INPUT_PULLUP);
  #ifdef IND_LED_PIN
  pinMode(IND_LED_PIN, OUTPUT);
  #endif

  Serial.begin(9600);
  
//  Ethernet.begin(mac,myIP);
  Ethernet.begin(mac,myIP,myDNS,myGW,myMASK);

  server.begin();
}

int last_millis = 0;

void loop() {
  if ((last_millis - millis()) >= 1000){
    read_sensors();
    last_millis = millis();
  }

  if (EthernetClient client = server.available())
    {
      handle_requests(client);      
      client.stop();
    }
}
