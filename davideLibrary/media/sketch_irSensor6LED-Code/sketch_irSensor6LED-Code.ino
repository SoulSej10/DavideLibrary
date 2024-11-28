// 

// Define pin numbers
const int IR_SENSOR_PIN = D0; // IR sensor connected to D0
const int LED_PINS[] = {D1, D2, D3, D4, D5, D6}; // LED pins
const int NUM_LEDS = 6; // Number of LEDs

void setup() {
  // Initialize the IR sensor pin
  pinMode(IR_SENSOR_PIN, INPUT);

  // Initialize the LED pins as OUTPUT and turn them ON
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], HIGH); // Turn ON all LEDs initially
  }

  // Optional: Begin serial communication for debugging
  Serial.begin(9600);
}

void loop() {
  // Read the IR sensor value
  int irValue = digitalRead(IR_SENSOR_PIN);

  if (irValue == HIGH) { // IR sensor detects something
    // Turn OFF all LEDs
    for (int i = 0; i < NUM_LEDS; i++) {
      digitalWrite(LED_PINS[i], LOW);
    }
    Serial.println("Object detected. LEDs OFF.");
  } else { // IR sensor does not detect anything
    // Turn ON all LEDs
    for (int i = 0; i < NUM_LEDS; i++) {
      digitalWrite(LED_PINS[i], HIGH);
    }
    Serial.println("No object detected. LEDs ON.");
  }
}
