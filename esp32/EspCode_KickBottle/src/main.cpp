#include <Arduino.h>
#include <EasyButton.h>   //inatall EasyButton from Library
#define SENSOR_CAPTURE    2
#define LED_LAMP          4
#define KICK_BOTTLE       5
#define SENSOR_KICK       22

unsigned long previousMillis = 0;
String data = "";
String dataSend = "CAPTURE"; //ข้อมูลที่จะส่งไปcomputerเพื่อให้ถ่ายภาพ
int delayBeforeKick = 300;   //ตั้งหน่วยเวลาก่อนเตะหลังจากเซ็นเซอร์จับขวดเจอ

bool flag = false; 
int capture = 0;
int sensorAvtive = 0;
int stateMachine = 1;
unsigned long previousKickTime = 0;
bool isKicking = false;
volatile unsigned long lastDebounceTimeMode = 0; // เวลาล่าสุดที่ debounce
volatile unsigned long debounceDelayMode = 100; // เวลา debounce (milliseconds)
EasyButton sensorCapture(SENSOR_CAPTURE);
void sendData();
int readSensor();

void SensorCaptureAvtive(){
  // Serial.println("SensorCaptureAvtive pressed");
  if ((millis() - lastDebounceTimeMode) > debounceDelayMode) {
    sensorAvtive = 1;
  }
  lastDebounceTimeMode = millis(); 
}

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_CAPTURE, INPUT_PULLUP);
  sensorCapture.onPressed(SensorCaptureAvtive);
  pinMode(LED_LAMP, OUTPUT);
  pinMode(KICK_BOTTLE, OUTPUT);
  pinMode(SENSOR_KICK, INPUT);
  digitalWrite(KICK_BOTTLE, HIGH);
}
void loop() {
  sensorCapture.read();
  if (stateMachine == 1) {
    if (sensorAvtive == 1) {
      sendData();
      sensorAvtive = 0;
    }
    stateMachine = 2;
  } else if (stateMachine == 2) {
    if (Serial.available() > 0) {
      data = Serial.readStringUntil('\n');
      data.trim();
      if (data == "NG") {
        flag = true; 
        digitalWrite(LED_LAMP, HIGH);
        while (flag) {
          if (readSensor() == 1 && !isKicking) {
            previousKickTime = millis();
            isKicking = true;
          }
          if (isKicking && millis() - previousKickTime >= delayBeforeKick) {
            digitalWrite(KICK_BOTTLE, LOW);
            Serial.println("-----------KICK_BOTTLE---------------");
            delay(100);
            digitalWrite(KICK_BOTTLE, HIGH);
            digitalWrite(LED_LAMP, LOW);
            isKicking = false;
            flag = false; 
          } else {
            digitalWrite(LED_LAMP, HIGH);
            digitalWrite(KICK_BOTTLE, HIGH);
          }
          sensorCapture.read();
          if(sensorAvtive == 1) {
            sendData();
            sensorAvtive = 0;
          }
        }
      } else {
        digitalWrite(LED_LAMP, LOW);
        digitalWrite(KICK_BOTTLE, HIGH);
      }
      data = ""; 
    }
    stateMachine = 1;
  }
}
void sendData() {
  Serial.println(dataSend);
  sensorAvtive = 0;
}

int readSensor() {
  int sensor_state = 0;
  sensor_state = digitalRead(SENSOR_KICK);
  // unsigned long currentMillis = millis();
  // if (currentMillis - previousMillis >= 50) {
  //   sensor_state = digitalRead(SENSOR_KICK);
  //   previousMillis = currentMillis; // Update previousMillis to currentMillis
  // }
  return sensor_state;
}
