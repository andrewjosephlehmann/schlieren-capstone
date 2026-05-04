#include <PID_v1.h>

/////////////////////
// Pin Definitions //
/////////////////////

const int selectPins[3] = {11, 12, 10};
const int zInput = A0;

const int extmon1 = A1;
const int extmon2 = A2;


const int relayPins[7]   = {2, 3, 4, 5, 6, 7, 8};
const int muxChannels[7] = {0, 2, 4, 3, 5, 6, 7};

const int RELAY_ON  = LOW;
const int RELAY_OFF = HIGH;

/////////////////////
// Thermistor
/////////////////////

const float SERIES_RESISTOR    = 100000.0;
const float NOMINAL_RESISTANCE = 100000.0;
const float NOMINAL_TEMP       = 25.0;
const float B_COEFFICIENT      = 3950.0;

/////////////////////
// PID
/////////////////////

double Setpoint[7];
double Input[7];
double Output[7];


// External thermistors // 
double mon1;
double mon2;

double Kp = 1;
double Ki = 0.5;
double Kd = 0;

PID pid[7] = {
  PID(&Input[0], &Output[0], &Setpoint[0], Kp, Ki, Kd, DIRECT),
  PID(&Input[1], &Output[1], &Setpoint[1], Kp, Ki, Kd, DIRECT),
  PID(&Input[2], &Output[2], &Setpoint[2], Kp, Ki, Kd, DIRECT),
  PID(&Input[3], &Output[3], &Setpoint[3], Kp, Ki, Kd, DIRECT),
  PID(&Input[4], &Output[4], &Setpoint[4], Kp, Ki, Kd, DIRECT),
  PID(&Input[5], &Output[5], &Setpoint[5], Kp, Ki, Kd, DIRECT),
  PID(&Input[6], &Output[6], &Setpoint[6], Kp, Ki, Kd, DIRECT)
};

/////////////////////
// Timing
/////////////////////

const int WindowSize = 1000;
unsigned long windowStartTime;

/////////////////////
// Serial Buffer
/////////////////////

#define CMD_BUFFER 40
char commandBuffer[CMD_BUFFER];
byte commandIndex = 0;

/////////////////////
// Setup
/////////////////////

void setup() {

  Serial.begin(9600);

  windowStartTime = millis();

  for (int i = 0; i < 3; i++) {
    pinMode(selectPins[i], OUTPUT);
    digitalWrite(selectPins[i], LOW);
  }

  pinMode(zInput, INPUT);

  for (int i = 0; i < 7; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], RELAY_OFF);

    Setpoint[i] = 0.0;

    pid[i].SetOutputLimits(0, WindowSize);
    pid[i].SetSampleTime(1000);
    pid[i].SetMode(AUTOMATIC);
  }

}

/////////////////////
// Main Loop
/////////////////////

void loop() {

  readSerialCommands();

  // Read sensors
  for (int i = 0; i < 7; i++) {
    Input[i] = readThermistor(muxChannels[i]);
  }

  mon1 = readThermistorDirect(extmon1);
  mon2 = readThermistorDirect(extmon2);
  
  // Compute PID
  for (int i = 0; i < 7; i++) {
    pid[i].Compute();
  }

  // Update window
  unsigned long now = millis();
  if (now - windowStartTime > WindowSize) {
    windowStartTime += WindowSize;
  }
  unsigned long elapsed = now - windowStartTime;

  // Heater control
  for (int i = 0; i < 7; i++) {

    // Safety: shut off on invalid reading
    if (Input[i] < -50 || Input[i] > 150) {
      digitalWrite(relayPins[i], RELAY_OFF);
      continue;
    }

    // Safety: shut off if far above setpoint
    if (Input[i] > Setpoint[i] + 15) {
      digitalWrite(relayPins[i], RELAY_OFF);
      continue;
    }

    if (elapsed < Output[i]) {
      digitalWrite(relayPins[i], RELAY_ON);
    } else {
      digitalWrite(relayPins[i], RELAY_OFF);
    }

  }

  // Output temperatures
  Serial.print("DATA");
  for (int i = 0; i < 7; i++) {
  Serial.print(",");
  Serial.print(Input[i], 1);
  }
  Serial.print(",");
  Serial.print(mon1,1);
  Serial.print(",");
  Serial.print(mon2,1);

  Serial.println();

  delay(50);

}

/////////////////////
// Thermistor
/////////////////////

float readThermistor(int muxChannel) {

  selectMuxPin(muxChannel);

  analogRead(zInput);
  delayMicroseconds(50);

  int raw = analogRead(zInput);

  if (raw == 0) return -999;

  float resistance = SERIES_RESISTOR * (1023.0 / raw - 1.0);

  // Steinhart-Hart equation
  float steinhart = log(resistance / NOMINAL_RESISTANCE);
  steinhart /= B_COEFFICIENT;
  steinhart += 1.0 / (NOMINAL_TEMP + 273.15);

  return (1.0 / steinhart) - 273.15;

}

float readThermistorDirect(int analogPin) {

  int raw = analogRead(analogPin);

  if (raw == 0) return -999;

  float resistance = SERIES_RESISTOR * (1023.0 / raw - 1.0);

  float steinhart = log(resistance / NOMINAL_RESISTANCE);
  steinhart /= B_COEFFICIENT;
  steinhart += 1.0 / (NOMINAL_TEMP + 273.15);

  return (1.0 / steinhart) - 273.15;
}

void selectMuxPin(byte pin) {
  for (int i = 0; i < 3; i++) {
    digitalWrite(selectPins[i], (pin & (1 << i)) ? HIGH : LOW);
  }
}

/////////////////////
// Serial Commands
/////////////////////

void readSerialCommands() {

  while (Serial.available()) {

    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      commandBuffer[commandIndex] = '\0';
      if (commandIndex > 0) {         // ignore blank lines
        parseCommand(commandBuffer);
      }
      commandIndex = 0;
    } else {
      if (commandIndex < CMD_BUFFER - 1) {
        commandBuffer[commandIndex++] = c;
      }
    }

  }

}

void parseCommand(char *cmd) {

  char *token = strtok(cmd, ",");

  if (token == NULL || strcmp(token, "SET") != 0) {
    Serial.println("ERR:CMD");
    return;
  }

  token = strtok(NULL, ",");
  if (token == NULL) {
    Serial.println("ERR:CHANNEL");
    return;
  }
  int ch = atoi(token);

  token = strtok(NULL, ",");
  if (token == NULL) {
    Serial.println("ERR:VALUE");
    return;
  }
  float sp = atof(token);

  if (ch < 0 || ch >= 7) {
    Serial.println("ERR:CHANNEL");
    return;
  }

  Setpoint[ch] = sp;

  pid[ch].SetMode(MANUAL);
  Output[ch] = 0;
  pid[ch].SetMode(AUTOMATIC);

  Serial.print("SETPOINT ");
  Serial.print(ch);
  Serial.print(" -> ");
  Serial.println(sp);

}