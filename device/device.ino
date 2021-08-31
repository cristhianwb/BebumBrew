
// Inlcui a biblioteca Dimmer
#include "Dimmer.h"
#include <DallasTemperature.h>
#include <avr/wdt.h>
#include "./crc.h"

#define DEV_SYNC   0xDDEE
#define ERRORS_ALLOWED 5
#define TIMEOUT        10000

#define ONE_WIRE_BUS 5

#define CM_SYNC  0xf1
#define CM_TEMP  0xf2
#define CM_PUMP  0xf3
#define CM_ERROR 0xff
#define CM_OK    0x33

typedef struct _packet{
  long heater_power;
  long pump_power;
  double temp;
  double temp2;
  uint8_t pad[3];
  crc crc_code;
} packet;


OneWire oneWire(ONE_WIRE_BUS);
Dimmer heater(3);
DallasTemperature sensors(&oneWire);
DeviceAddress sensor1, sensor2;
double last_temp = 0;
long heater_power = 0;
int error_count = ERRORS_ALLOWED; /*number of consecutive erros allowed*/
unsigned long last_rcv;

void setup(){
  pinMode(13, OUTPUT);
  establish_connection();
  /*Enable watchdog*/
  sensors.begin();
  sensors.setWaitForConversion(false);
  pinMode(6, OUTPUT);
  sensors.getAddress(sensor1, 0);
  sensors.getAddress(sensor2, 1); 
  sensors.requestTemperatures();
  heater.begin();
    
}

void establish_connection(){
  packet pkt;
  bool is_connected = false;
  Serial.begin(9600);
  while (!Serial);

  while (!is_connected){
    digitalWrite(13, 1);
    if (Serial.available() > 0 ){ 
      if ( ( Serial.readBytes( (byte*) &pkt, sizeof(packet))  == sizeof(packet) ) && is_valid_checksum(&pkt) ) {
        Serial.flush();
        if (pkt.heater_power != DEV_SYNC)
          continue;
        
        memset(&pkt, 0, sizeof(packet));
        pkt.pump_power = ~DEV_SYNC;
        pkt.crc_code = crcFast((byte*) &pkt, sizeof(packet) - sizeof(crc) );
        delay(100);
        Serial.write((byte*) &pkt, sizeof(packet));
        memset(&pkt, 0, sizeof(packet));
        delay(1000);
        if ( (Serial.available() > 0) && ( Serial.readBytes( (byte*) &pkt, sizeof(packet))  == sizeof(packet) ) && is_valid_checksum(&pkt) && pkt.pump_power == DEV_SYNC)
          is_connected = true;
      }
    }
    digitalWrite(13, 0);
  }
  
}

bool is_valid_checksum(packet* pkt){
  return crcFast((byte*) pkt, sizeof(packet) - sizeof(crc) ) == pkt->crc_code;
}

void loop(){
  int i;
  packet pkt;
  
  if (Serial.available() > 0 ){
      
      if ( ( Serial.readBytes( (byte*) &pkt, sizeof(packet))  == sizeof(packet) ) && is_valid_checksum(&pkt) ){
        if (pkt.temp == 0){
        
          if (pkt.heater_power != heater_power){
            heater.set(pkt.heater_power);
            heater_power = pkt.heater_power;
          }
          analogWrite(6, pkt.pump_power);
          memset(&pkt, 0, sizeof(packet));
          if (sensors.isConversionComplete()){
            pkt.temp = sensors.getTempC(sensor1);
            pkt.temp2 = sensors.getTempC(sensor2);
          }
          sensors.requestTemperatures();
          pkt.crc_code = crcFast((byte*) &pkt, sizeof(packet) - sizeof(crc) );
          //Reset the error counter
          error_count = ERRORS_ALLOWED;
          last_rcv = millis();
        }else if (pkt.temp == -1) {
          error_count = 0; //Forces establish_connection()
        }else{
          error_count--;
        }
           
      }else{
        memset(&pkt, 0, 16);
        pkt.heater_power = -1;
        pkt.pump_power = -1;
        pkt.temp = -1.0;
        error_count--;       
      }
      Serial.flush();
      Serial.write((byte*) &pkt, sizeof(packet));
  }

  if ( (error_count <= 0) || (  (millis() - last_rcv) >  TIMEOUT) ) {
    Serial.end();
    establish_connection();
  }  
  
}
