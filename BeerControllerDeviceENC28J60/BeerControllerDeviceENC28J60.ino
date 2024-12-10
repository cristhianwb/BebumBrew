#define MACADDRESS 0x00,0x01,0x02,0x03,0x04,0x05
#define MYIPADDR 192,168,1,6
#define MYIPMASK 255,255,255,0
#define MYDNS 192,168,1,1
#define MYGW 192,168,1,1
#define LISTENPORT 1000
#define UARTBAUD 9600
#define ACTLOGLEVEL LOG_INFO


#include <UIPEthernet.h>
#include <Arduino_JSON.h>


EthernetServer server = EthernetServer(LISTENPORT);


void setup() {

  uint8_t mac[6] = {MACADDRESS};
  uint8_t myIP[4] = {MYIPADDR};
  uint8_t myMASK[4] = {MYIPMASK};
  uint8_t myDNS[4] = {MYDNS};
  uint8_t myGW[4] = {MYGW};
  
  Serial.begin(9600);
  
//  Ethernet.begin(mac,myIP);
  Ethernet.begin(mac,myIP,myDNS,myGW,myMASK);

  server.begin();
}


void handle_requests(EthernetClient client){
  char method[5];
  char *http_ver_pos, *path_pos, *path;
  char *msg;
  size_t size, tmp_size;

  size = client.available();
  
  if(size > 0){
    msg = (char*) calloc(size+1, sizeof(char*));
    size = client.read(msg, size);
    //find http version header
    http_ver_pos = strstr(msg, "HTTP/1.1");
    if (http_ver_pos != NULL){
      //find path
      for (path_pos = msg; ((*path_pos != '/') && (path_pos < http_ver_pos)); path_pos++);
      if (path_pos < http_ver_pos){
        //Copy method from HEADER
        tmp_size = path_pos - msg;
        method[tmp_size-1] = 0;
        memcpy(method, msg, tmp_size-1);
        Serial.print("Method: ");
        Serial.write(method, tmp_size);
        Serial.println("");
        
        //Copy path from HEADER       
        tmp_size = http_ver_pos - path_pos;
        path = calloc(tmp_size, sizeof(char*));
        path[tmp_size-1] = 0;
        memcpy(path, path_pos, tmp_size-1);
        Serial.print("Path: ");
        Serial.write(path, tmp_size);      
        Serial.println("");
      }
    }
    Serial.write(msg, size);
    Serial.print("Size: ");
    Serial.println(size);
    free(msg);
  }

   
}

void loop() {

  if (EthernetClient client = server.available())
    {
      Serial.println("DATA from Client: "); 
      
      handle_requests(client);      
      
      client.stop();
    }
}
