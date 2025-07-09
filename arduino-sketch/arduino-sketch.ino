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
  if (Serial.available() > 0) {
    char c = Serial.read();

    if (c == 'U') {
      ledVals[selectedLED] = min(255, ledVals[selectedLED] + 10);
    } 
    else if (c == 'D') {
      ledVals[selectedLED] = max(0, ledVals[selectedLED] - 10);
    }
    else if (c >= '1' && c <= '5') {
      selectedLED = c - '1';
      Serial.print("Selected LED ");
      Serial.println(selectedLED + 1);
    }

    ledVals[selectedLED] = constrain(ledVals[selectedLED], 0, 255);
    analogWrite(ledPins[selectedLED], ledVals[selectedLED]);
  }
}
