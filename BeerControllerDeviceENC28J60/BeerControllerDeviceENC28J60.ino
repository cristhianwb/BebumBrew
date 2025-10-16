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
#include "UserTimer.h"

//Device Pin Out Definition
#define PUMP_MOSFET_PIN   13
#define ONE_WIRE_BUS_PIN  10
#define LEVEL_SENSOR_PIN  12
#define HEATER_TRIAC_PIN  3
//#define IND_LED_PIN       0
//#define DIMMER_ZERO_CROSS_PIN       2 (Defined in Dimmer.h)

#define READ_ATTEMPTS 15
#define PUMP_POWER_MIN  5

typedef enum {GET, POST} METHOD;

//Variaveis globais dos sensores e atuadores
int heater_power = 0;
double temp_sensor1 = 0;
double temp_sensor2 = 0;
//pump control variables
bool level_sensor_reached = false;  //Indica quando o sensor atingir o limite da panela
bool level_control_on = false;      //Indica se deve controlar o nivel da panela pela bomba utilizando o sensor de nivel
bool level_switch_nf = false;       //Indica se o nível é atingido quando o sensor fecha ou abre 
int pump_power = 0;                      //Potência da bomba
int current_pump_power = 0;            //Potência da bomba atual 
uint8_t pump_power_level_reached = 0;        //Potência da bomba quando o nível é atingido
bool pump_burst_en = false;           //Potencia maxima na partida ativado
bool pump_burst = false;              //Potencia maxima acionada quando muda de 0 para qualquer valor > 0
uint8_t pump_burst_time = 5;          //Tempo em segundos com potência máxima
uint8_t burst_timer;                  //Timer de usuário para controlar o tempo de potência maxima
int p_power;                         
float time_between_level_switch = 0;      //Tempo entre mudança do nivel da panela (utiizado para calcular a vazão)
unsigned long last_millis_level_sensor = 0;

const unsigned long sampling_interval = 1000;

bool sensor1_read = false;
bool sensor2_read = false;

int read_attempts_counter_sen1 = READ_ATTEMPTS;
int read_attempts_counter_sen2 = READ_ATTEMPTS;

//Sensor temperatura
OneWire oneWire(ONE_WIRE_BUS_PIN);
DallasTemperature sensors(&oneWire);
DeviceAddress addr_sen1, addr_sen2;


//Dimmer (ZC Pin 2)
Dimmer heater(HEATER_TRIAC_PIN);
//Servidor
EthernetServer server = EthernetServer(LISTENPORT);

UserTimer timers;

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
    return true;
  }
  return false;  
}

bool set_int8_value(uint8_t value, uint8_t* variable, int min, int max){
  if ((value >= min) && (value <= max)){
    *variable = value;
    return true;
  }
  return false;
}

void respond(METHOD method, char* msg, EthernetClient client){
  char * response_cstr;
  JSONVar jsonObj, pump;
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
      
      if ((JSON.typeof(jsonObj["pump"]) == "object")){
        pump = jsonObj["pump"];
        Serial.println(pump);

        if ((JSON.typeof(pump["power"]) == "number") && set_pump_power(pump["power"])){
          Serial.print("Pump power changed to : ");
          Serial.println(pump_power);
        }

        if ((JSON.typeof(pump["power_level_reached"]) == "number") && set_int8_value(pump["power_level_reached"], &pump_power_level_reached, 0, 100)){
          Serial.print("power_level_reached changed to : ");
          Serial.println(pump_power_level_reached);
        }

        if ((JSON.typeof(pump["burst_time"]) == "number") && set_int8_value(pump["burst_time"], &pump_burst_time, 1, 10)){
          timers.setTime(pump_burst_time * 1000, burst_timer);
          Serial.print("pump_burst_time changed to : ");
          Serial.println(pump_burst_time);
        }

        if (JSON.typeof(pump["level_control"]) == "boolean"){
          level_control_on = pump["level_control"];
          Serial.print("level_control_on changed to : ");
          Serial.println(level_control_on ? "True" : "False");
        }

        if (JSON.typeof(pump["level_switch_nf"]) == "boolean"){
          level_switch_nf = pump["level_switch_nf"];
          Serial.print("level_switch_nf changed to : ");
          Serial.println(level_switch_nf ? "True" : "False");
        }

        if (JSON.typeof(pump["burst"]) == "boolean"){
          pump_burst_en = pump["burst"];
          Serial.print("pump_burst_en changed to : ");
          Serial.println(pump_burst_en ? "True" : "False");
        }
      }              
    }
  }

  jsonResponse["temp1"] = temp_sensor1;
  jsonResponse["temp2"] = temp_sensor2;
  jsonResponse["level"] = level_sensor_reached;
  jsonResponse["pump_power"] = current_pump_power;
  jsonResponse["time_between_level_switch"] = time_between_level_switch;

  const char* const response_format_str = "HTTP/1.1 200 OK"
                                          "Content-Type: text/html"
                                          "Content-Length: %d\r\n\r\n%s";

  String json_response_str = JSON.stringify(jsonResponse);
  json_size = json_response_str.length();
  res_size = strlen(response_format_str) + json_size + 10;
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
    
    free(msg);
  }

   
}

bool read_sensors(){
  Serial.println("Reading sensors...");
  

  double temp_sens1 = 0;
  double temp_sens2 = 0;

  temp_sens1 =  sensors.getTempC(addr_sen1);
  temp_sens2 = sensors.getTempC(addr_sen2);
  
  // Serial.print("Read attempts Sen1: ");
  // Serial.println(read_attempts_counter_sen1);

  // Serial.print("Read attempts Sen1: ");
  // Serial.println(read_attempts_counter_sen2);


  if (temp_sens1 != -127){
    temp_sensor1 = temp_sens1;
    read_attempts_counter_sen1 = READ_ATTEMPTS;
  } else {
    read_attempts_counter_sen1--;
    if (read_attempts_counter_sen1 == 0){
      temp_sensor1 = 0;
      read_attempts_counter_sen1 = READ_ATTEMPTS;
    }      
  }

  if (temp_sens2 != -127){
    temp_sensor2 = temp_sens2;
    read_attempts_counter_sen2 = READ_ATTEMPTS;
  } else {
    read_attempts_counter_sen2--;
    if (read_attempts_counter_sen2 == 0){
      temp_sensor1 = 0;
      read_attempts_counter_sen2 = READ_ATTEMPTS;
    }
  }

  sensors.requestTemperatures();
  
  Serial.print("Pump power: ");
  Serial.println(p_power);
  Serial.print("Temp 1: ");
  Serial.println(temp_sensor1);
  Serial.print("Temp 2: ");
  Serial.println(temp_sensor2);
  
  return true;
}

bool finish_pump_burst(){
  Serial.println("Burst terminado");
  pump_burst = false;
  return false;
}

bool control_pump(){
  
  bool new_level = digitalRead(LEVEL_SENSOR_PIN) ^ level_switch_nf;
  
  //Cronometrar a mudança de nivel do sensor para calcular a vazão
  if (new_level != level_sensor_reached){
    unsigned long current_millis = millis();
    time_between_level_switch = (float) (current_millis - last_millis_level_sensor) / 1000.0;
    last_millis_level_sensor = current_millis;    
  }

  level_sensor_reached = new_level;

  int new_pump_power = (level_control_on && level_sensor_reached) ? pump_power_level_reached : pump_power;   

  if ((current_pump_power == 0) && (new_pump_power > 0) && pump_burst_en){
    Serial.println("Burst Started!");
    timers.startTimer(burst_timer);
    pump_burst = true;    
  }

  current_pump_power = new_pump_power;

  if (current_pump_power > 0){
    //Se tem burst ativado, deve ligar a bomba no maximo
    if (pump_burst) current_pump_power = 100;
    p_power = ((current_pump_power / 100.0) * (255.0 - PUMP_POWER_MIN)) + PUMP_POWER_MIN;       
  }else
    p_power = 0;

  
  analogWrite(PUMP_MOSFET_PIN, 255-p_power);
  return true;  
}

void setup() {

  uint8_t mac[6] = {MACADDRESS};
  uint8_t myIP[4] = {MYIPADDR};
  uint8_t myMASK[4] = {MYIPMASK};
  uint8_t myDNS[4] = {MYDNS};
  uint8_t myGW[4] = {MYGW};
  
  pinMode(PUMP_MOSFET_PIN, OUTPUT);
  analogWrite(PUMP_MOSFET_PIN, 255);
  pinMode(LEVEL_SENSOR_PIN, INPUT_PULLUP);
  #ifdef IND_LED_PIN
  pinMode(IND_LED_PIN, OUTPUT);
  #endif

  Serial.begin(9600);

  sensors.setWaitForConversion(false);
  sensors.begin();

  sensors.getAddress(addr_sen1, 0);
  sensors.getAddress(addr_sen2, 1);


  sensors.requestTemperatures();

  heater.begin();
  
  
//  Ethernet.begin(mac,myIP);
  Ethernet.begin(mac,myIP,myDNS,myGW,myMASK);

  server.begin();
  timers.addTimer(sampling_interval, true, read_sensors);
  timers.addTimer(50, true, control_pump);
  burst_timer = timers.addTimer(pump_burst_time * 1000, false, finish_pump_burst);
}


void loop() {

  timers.update();

  if (EthernetClient client = server.available())
    {
      handle_requests(client);      
      client.stop();
    }
}
