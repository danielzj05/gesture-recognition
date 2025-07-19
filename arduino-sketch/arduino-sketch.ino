const int ledPins[5] = {5, 6, 9, 10, 11};
int ledVals[5] = {0, 0, 0, 0, 0};
int selectedLED = 0;

void setup() {
  Serial.begin(250000);
  for (int i = 0; i < 5; i++) {
    pinMode(ledPins[i], OUTPUT);
    analogWrite(ledPins[i], 0);
  }
}

void loop() {
  if (Serial.available() >= 5) { // Wait for 5 bytes
    for (int i = 0; i < 5; i++) {
      ledVals[i] = Serial.read();
      analogWrite(ledPins[i], ledVals[i]);
    }
  }
}
