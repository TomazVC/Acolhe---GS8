/* Acolhe experimental Uno + L298N + LCD1602 + PIR A0.
 * SOURCE ONLY: NOT uploaded or physically validated.
 * Motors are ALWAYS disabled in this reference firmware.
 * Protocol at 9600: ? status, p presence, y correct, n retry, x stop.
 * ACK describes logic only, never proof of physical output.
 */
#include <LiquidCrystal.h>
LiquidCrystal lcd(8, 9, 10, 11, 12, 13);
const uint8_t PIR_PIN = A0;
const uint8_t MOTOR_PINS[] = {2, 3, 4, 5, 6, 7};
void stopMotors() {
  for (uint8_t i = 0; i < 6; ++i) digitalWrite(MOTOR_PINS[i], LOW);
}
void setup() {
  for (uint8_t i = 0; i < 6; ++i) pinMode(MOTOR_PINS[i], OUTPUT);
  stopMotors();
  pinMode(PIR_PIN, INPUT);
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.print("Acolhe seguro");
}
void loop() {
  stopMotors();
  if (!Serial.available()) return;
  const char cmd = Serial.read();
  const bool present = digitalRead(PIR_PIN) == HIGH;
  if (cmd == '?') Serial.println(F("ACOLHE_SAFE_V1 MOTORS_DISABLED"));
  else if (cmd == 'p') Serial.println(present ? F("PRESENT=1") : F("PRESENT=0"));
  else if (cmd == 'x') { stopMotors(); Serial.println(F("STOPPED")); }
  else if (cmd == 'y' || cmd == 'n') {
    lcd.clear();
    lcd.print(present ? (cmd == 'y' ? "Muito bem!" : "Vamos tentar!") : "Aguardando...");
    Serial.println(F("ACK_LOGIC_ONLY MOTORS_DISABLED"));
  } else Serial.println(F("ERR_COMMAND"));
}
