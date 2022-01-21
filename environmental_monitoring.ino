// Load Wi-Fi library
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include "ESP8266WebServer.h"
#include <ESP8266HTTPClient.h>

// Set web server port number to 80
ESP8266WebServer server(80);

HTTPClient http;  //Declare an object of class HTTPClient
WiFiClient _client;

// Replace with your network credentials
const char* ssid     = "WLAN";
const char* password = "";

//using ESP8266 with Adafruit DHT11 library: 
//https://github.com/adafruit/DHT-sensor-library
#include "DHT.h"
// connect data pin of DHT11 to D2 ESP8266 NodeMCU
#define DHTPIN D2    

#define DHTTYPE DHT11   // DHT 11

DHT dht(DHTPIN, DHTTYPE);
bool led_status=false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);
  dht.begin();
  // Connect to Wi-Fi network with SSID and password
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
  }
  // Print local IP address and start web server
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  server.begin();
    
  Serial.println("Booting");
  Serial.println("Ready");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());  
}

void req(float t, float h){
    if (WiFi.status() == WL_CONNECTED) { //Check WiFi connection status
        String geturl =  "http://iuriier.pythonanywhere.com/load_data/";
        Serial.println(geturl);
        http.begin(_client, geturl);  //Specify request destination
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");

        //Post Data
        String postData = "temperature=" + String(t) + "&humidity=" + String(h);
        int httpCode = http.POST(postData);   //Send the request
  
        if (httpCode > 0) { //Check the returning code
            String payload = http.getString();   //Get the request response payload
            Serial.println(payload);             //Print the response payload
        }
        http.end();   //Close connection
    }
}

int get_new_interval(){
    if (WiFi.status() == WL_CONNECTED) { //Check WiFi connection status
        String geturl =  "http://iuriier.pythonanywhere.com/config/";
        http.begin(_client, geturl);  //Specify request destination
        int httpCode = http.GET();                                  //Send the request
        
        if (httpCode > 0) { //Check the returning code
            int payload = http.getString().toInt();   //Get the request response payload
            return payload;
        }
        http.end();   //Close connection
    }
    return 15000;
}

int interval = 15000;
unsigned long currentTime;
unsigned long previousTime = 0;

void loop() {
  server.handleClient();
    
  currentTime = millis();
  
  led_status=!led_status;

  interval = get_new_interval();
  
  if(currentTime - previousTime > interval){
     float h = dht.readHumidity();     // get humidity
     float t = dht.readTemperature();  // get temperature
     
     if ( !isnan(h) && !isnan(t)) {
        Serial.print("Humidity: ");
        Serial.print(h);
        Serial.print(" %  Temperature: ");
        Serial.print(t);
        Serial.println(" *C ");
     }
     
     previousTime = currentTime;
     req(t, h);
     digitalWrite(LED_BUILTIN,led_status);
  }
}
