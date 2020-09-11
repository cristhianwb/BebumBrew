
// Inlcui a biblioteca Dimmer
#include "Dimmer.h"
#include <DallasTemperature.h>
#include "./crc.h"


#define ONE_WIRE_BUS 5

#define CM_POWER 0xf1
#define CM_TEMP  0xf2
#define CM_PUMP  0xf3
#define CM_ERROR 0xff
#define CM_OK    0x33

typedef struct _packet{
  long heater_power;
  long pump_power;
  double temp;
  uint8_t pad[3];
  crc crc_code;
} packet;


OneWire oneWire(ONE_WIRE_BUS);
Dimmer heater(3);
DallasTemperature sensors(&oneWire);
DeviceAddress sensor1;
double last_temp = 0;
long heater_power = 0;

void setup(){

  Serial.begin(9600);
  while (!Serial);
  
  sensors.begin();
  sensors.setWaitForConversion(false);
  pinMode(6, OUTPUT);
  sensors.getAddress(sensor1, 0); 
  sensors.requestTemperatures();
  heater.begin();
    
}

bool is_valid_checksum(packet* pkt){
  return crcFast((byte*) pkt, sizeof(packet) - sizeof(crc) ) == pkt->crc_code;
}

void loop(){
  int i;
  packet pkt;
  
  if (Serial.available() > 0 ){
      
      if ( ( Serial.readBytes( (byte*) &pkt, sizeof(packet))  == sizeof(packet) ) && is_valid_checksum(&pkt) ){
        if (pkt.heater_power != heater_power){
          heater.set(pkt.heater_power);
          heater_power = pkt.heater_power;
        }
        analogWrite(6, pkt.pump_power);
        memset(&pkt, 0, 16);
        pkt.temp = sensors.isConversionComplete() ? sensors.getTempC(sensor1) : 0;
        sensors.requestTemperatures();
        pkt.crc_code = crcFast((byte*) &pkt, sizeof(packet) - sizeof(crc) );
      }else{
        memset(&pkt, 0, 16);
        pkt.heater_power = -1;
        pkt.pump_power = -1;
        pkt.temp = -1.0;       
      }
      Serial.flush();
      Serial.write((byte*) &pkt, sizeof(packet));
  }
  
}
