#include <TimerOne.h>
#include <TM1637Display.h>

String operation = "";
String inputString = "";
String last_operation = "";
String next_operation = "";

bool calibration = false;


volatile int x = 0;
volatile int y = 0;
volatile int z = 0;
int value = 0;
int number = 0;
volatile byte stanje = 0;
//const int VCCPin = A0;
const int xPin = A0;
const int yPin = A1;
const int zPin = A2;

const int TOUCH_PIN = 2;

const int rLED = 3;
const int gLED = 11;

const int CLK = 9;
const int DIO = 8;

TM1637Display display(CLK, DIO);



void setup() {
  Serial.begin(9600);
  Timer1.initialize(1000000);
  Timer1.attachInterrupt(timerIsr);
  //Timer1.attachInterrupt(digitalPinInterrupt(TOUCH_PIN),acquisition, CHANGE);
  pinMode(TOUCH_PIN, INPUT);

  display.setBrightness(7);
}

void loop() {
  if (operation == "X"){
    value = axisCalibration(x);
    delay(100);
  }
  else if (operation == "Y"){
    value = axisCalibration(y);
    delay(100);
  }
  else if (operation == "Z"){
    value = axisCalibration(z);
    delay(100);
  }
  else if (operation == "LET"){
    ledDiode();
  }

  if (calibration){
    if (digitalRead(TOUCH_PIN) == HIGH){
      printValue();
      calibration = false;
    }
  }

}

void ledDiode(){
  while (operation != "Kraj letenja"){
    int x = number;
    if (x < 0){
      analogWrite(rLED, abs(x));
    }
    else analogWrite(gLED, abs(x));
    display.showNumberDec(abs(x));
    delay(100);
  }
}

void printValue(){
  Serial.println("cmks");
  for (int i = 0; i < 5; i++){
      Serial.print("x:");
      Serial.print(x);
      Serial.print(",y:");
      Serial.print(y);
      Serial.print(",z:");
      Serial.print(z);
      Serial.print("\n");
      delay(100);
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    Serial.println(inChar);
    if (inChar == '\n'){
      
      operation = inputString;
      number = 0;
      if (inputString == "X" || inputString == "Y" || inputString == "Z") calibration = true;
      inputString = "";
    }
    else if (inChar >= '0' && inChar <= '9') {
        number = number * 10 + inChar - '0';
    }
    else {
      inputString += inChar;
    }
  }
}


int axisCalibration(int value){
  if (stanje == 1){
      display.showNumberDec(value);
      stanje = 0;
  }

  return value;
}

void timerIsr(){
  x = analogRead(xPin);
  y = analogRead(yPin);
  z = analogRead(zPin);
  stanje = 1;
}
