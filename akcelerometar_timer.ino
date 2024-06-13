#include <TimerOne.h>
#include <TM1637Display.h>

String operation = "";
String inputString = "";
String last_operation = "";
String next_operation = "";
int num1 = 0;
bool calibration = false;
bool negative = false;
bool flag = false;

volatile int x = 0;
volatile int y = 0;
volatile int z = 0;
int value = 0;
int number = 0;
volatile byte stanje = 0;

const int xPin = A0;
const int yPin = A1;
const int zPin = A2;

const int TOUCH_PIN = 2;

const int rLED = 3;
const int gLED = 11;

const int CLK = 9;
const int DIO = 8;

TM1637Display display(CLK, DIO);

void setup()
{
  Serial.begin(9600);
  Timer1.initialize(100000);
  Timer1.attachInterrupt(timerIsr);
  pinMode(TOUCH_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(TOUCH_PIN), takeValue, CHANGE);
  pinMode(rLED, OUTPUT);

  pinMode(gLED, OUTPUT);

  display.setBrightness(7);
}

void loop()
{
  if (operation == "calibrateX")
  {
    value = axisCalibration(x);
  }
  else if (operation == "calibrateY")
  {
    value = axisCalibration(y); 
  }
  else if (operation == "calibrateZ")
  {
    value = axisCalibration(z);
  }
  else if (operation == "start")
  {
    ledDiode();
  }
}


//slanje brojeva tokom kalibracije
void takeValue()
{
  if (calibration)
  {
    printValue();
    calibration = false;
  }
}

//letenje
void ledDiode()
{
  printValue();
  while (operation != "kraj letenja")
  {
    serialEvent();
    if (negative)
    {
      analogWrite(rLED, number);
      analogWrite(gLED, 0);
    }
    else
    {
      analogWrite(gLED, number);
      analogWrite(rLED, 0);
    }
    printValue();
    display.showNumberDec(number);
  }
  analogWrite(rLED, 0);
  analogWrite(gLED, 0);
}

//slanje ocitanih vrednosti sa akcelometra
void printValue()
{
  for (int i = 0; i < 5; i++)
  {
    Serial.print("x:");
    Serial.print(x);
    Serial.print(",y:");
    Serial.print(y);
    Serial.print(",z:");
    Serial.print(z);
    Serial.print("\n");
  }
}

//citanje sa serial monitora
void serialEvent()
{
  while (Serial.available())
  {
    char inChar = (char)Serial.read();
    //ako smo stigli do kraja reda to je jedna komanda
    if (inChar == '\n')
    {

      operation = inputString;
      number = num1;
      num1 = 0;
      negative = flag;
      flag = false;
      //kalibracija
      if (inputString == "calibrateX" || inputString == "calibrateY" || inputString == "calibrateZ")
        calibration = true;
      inputString = "";
    }
    //u slucaju da je broj negativan
    else if (inChar == '-')
      flag = true;
    //citanje brojeva
    else if (inChar >= '0' && inChar <= '9')
    {
      num1 = num1 * 10 + inChar - '0';
    }
    else
    {
      inputString += inChar;
    }
  }
}

//prikaz na displeju
int axisCalibration(int value)
{
  if (stanje == 1)
  {
    display.showNumberDec(value);
    stanje = 0;
  }

  return value;
}


//citanje podataka sa akcelometra
void timerIsr()
{
  x = analogRead(xPin);
  y = analogRead(yPin);
  z = analogRead(zPin);
  stanje = 1;
}
