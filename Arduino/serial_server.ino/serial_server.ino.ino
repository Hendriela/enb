/*
  Serial Server
     - Respond to single character commands received via serial
*/

#include "pitches.h"

// Define pins
#define MOTOR_LEFT 9
#define MOTOR_RIGHT 3
#define FORWARD_LEFT 2
#define BACKWARD_LEFT 4
#define FORWARD_RIGHT 7
#define BACKWARD_RIGHT 8 
#define EYE_RIGHT 0
#define EYE_LEFT 1
#define SPEAKER 11



void setup() {
  // initialize serial port
  Serial.begin(19200);

  // Initialize output pins
  pinMode(FORWARD_LEFT, OUTPUT);
  pinMode(FORWARD_RIGHT, OUTPUT);
  pinMode(BACKWARD_LEFT, OUTPUT);
  pinMode(BACKWARD_RIGHT, OUTPUT);

  // go forward initially
  analogWrite(MOTOR_RIGHT, 0);
  analogWrite(MOTOR_LEFT, 0);
  forward_left();
  forward_right();

  play_startup();
}

void loop() {
  
  // Check for any incoming bytes
  if (Serial.available() > 0) {
    char wheel = Serial.read();
    String voltage = Serial.readStringUntil(';');

    int volt = voltage.toInt();

    Serial.println(wheel);
    Serial.println(volt);

    // Respond to command "w" -> forward
    if(wheel == 'w') {
      forward_left();
      forward_right();
      analogWrite(MOTOR_RIGHT, 255);
      analogWrite(MOTOR_LEFT, 255);
    }

    // Respond to command "s" -> backward
    if(wheel == 's') {
      backward_left();
      backward_right();
      analogWrite(MOTOR_RIGHT, 255);
      analogWrite(MOTOR_LEFT, 255);
    }

    // Respond to command "a" -> sharp left turn
    if(wheel == 'a') {    
      forward_left();
      backward_right();
      analogWrite(MOTOR_RIGHT, 255);
      analogWrite(MOTOR_LEFT, 255);
    }
    
    // Respond to command "d" -> sharp right turn
    if(wheel == 'd') {    
      backward_left();
      forward_right();
      analogWrite(MOTOR_RIGHT, 255);
      analogWrite(MOTOR_LEFT, 255);
    }

    // Respond to command "e" -> slight right turn
    if(wheel == 'e') {    
      analogWrite(MOTOR_RIGHT, 255/2);
      analogWrite(MOTOR_LEFT, 255);
    }
    
    // Respond to command "e" -> slight left turn
    if(wheel == 'q') {  
      analogWrite(MOTOR_RIGHT, 255);
      analogWrite(MOTOR_LEFT, 255/2);
    }

    // Respond to command "t" -> stop (terminate)
    if(wheel == 't') {      
      analogWrite(MOTOR_RIGHT, 0);
      analogWrite(MOTOR_LEFT, 0);
      play_shutdown();
    }                                                                                                                                                                                                                                                                      
    
  }

  // Wait a bit
  delay(10);
}


void forward_left(){
  digitalWrite(FORWARD_LEFT, HIGH);
  digitalWrite(BACKWARD_LEFT, LOW);
  }

void backward_left(){
  digitalWrite(FORWARD_LEFT, LOW);
  digitalWrite(BACKWARD_LEFT, HIGH);
  }

void forward_right(){
  digitalWrite(FORWARD_RIGHT, HIGH);
  digitalWrite(BACKWARD_RIGHT, LOW);
  }

void backward_right(){
  digitalWrite(FORWARD_RIGHT, LOW);
  digitalWrite(BACKWARD_RIGHT, HIGH);
  }


void play_startup() {  

  // Initialize sequence of notes
  int melody[] = {
    NOTE_DS6, NOTE_DS5, NOTE_B5, NOTE_GS5, NOTE_DS6, NOTE_B5
  };
  
  int noteDurations[] = {
    6, 8, 4, 3, 4, 2
  };
  
  for (int thisNote = 0; thisNote < 6; thisNote++) {
    // to calculate the note duration, take one second divided by the note type.
    //e.g. quarter note = 1000 / 4, eighth note = 1000/8, etc.
    int noteDuration = 1000 / noteDurations[thisNote];

    tone(SPEAKER, melody[thisNote], noteDuration);
    // to distinguish the notes, set a minimum time between them.

    // the note's duration + 30% seems to work well:
    int pauseBetweenNotes = noteDuration * 1.30;

    delay(pauseBetweenNotes);
    // stop the tone playing:
    noTone(SPEAKER);
  }
}


void play_shutdown() {  
  // Initialize sequence of notes
  int melody[] = {
    NOTE_GS5, NOTE_DS5, NOTE_GS4, NOTE_B4
  };
  
  int noteDurations[] = {
    6, 6, 6, 4
  };
  
  for (int thisNote = 0; thisNote < 4; thisNote++) {
    // to calculate the note duration, take one second divided by the note type.
    //e.g. quarter note = 1000 / 4, eighth note = 1000/8, etc.
    int noteDuration = 1000 / noteDurations[thisNote];

    tone(SPEAKER, melody[thisNote], noteDuration);
    // to distinguish the notes, set a minimum time between them.

    // the note's duration + 30% seems to work well:
    int pauseBetweenNotes = noteDuration * 1.30;

    delay(pauseBetweenNotes);
    // stop the tone playing:
    noTone(SPEAKER);
  }
}
