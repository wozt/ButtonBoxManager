// Définition des broches utilisées pour les boutons
const int boutons[12] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, A1};
// Correspondance touches F13-F24
const char* touches[12] = {"F13", "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24"};

void setup() {
  Serial.begin(9600);

  // Configurer chaque bouton en INPUT_PULLUP
  for (int i = 0; i < 12; i++) {
    pinMode(boutons[i], INPUT_PULLUP);
  }
}

void loop() {
  for (int i = 0; i < 12; i++) {
    if (digitalRead(boutons[i]) == LOW) {  // Si bouton pressé
      Serial.println(touches[i]);  // Envoie la touche correspondante
      delay(300);  // Anti-rebond
    }
  }
}
