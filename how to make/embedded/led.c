//this code was built for the ATTiny 44 to make 2 LEDs blink in sequence
//By Océane Boulais for HTMAA 2018

#include <avr/io.h>

#define led_pin1 (1 << PA2) //pin 11
#define led_pin2 (1 << PA3) //pin 10
#define button_pin (1 << PB2) //pin 5

int main(void) {
    // Configure led_pin1 as an output.
    DDRA |= led_pin1;
    // Configure led_pin2 as an output.
    DDRA |= led_pin2;
    // Configure button_pin as an input.
    DDRB &= ~button_pin;
    // Activate button_pin's pullup resistor.
    PORTB |= button_pin;

    // Set led_pin1 high.
    PORTA |= led_pin1;
      // Set led_pin2 high.
    PORTA |= led_pin2;

    // start the loop!
    while (1) {
        // Turn on the LED1 when the button is pressed.
        if (PINB & button_pin) { //check the bits in register PINB
            // Turn off the LED1, turn on LED2.
            PORTA &= ~led_pin1; //turning off LED1. ANDing (&=) sets the bits in register PORTA to 0
            PORTA |= led_pin2; // turning on LED2. ORing (|=) sets the bit to led_pin2 value
            
        } else {
            PORTA &= ~led_pin2; //turning off LED2. 
            PORTA |= led_pin1; // turning on LED1. ANDing (&=) sets the bits in register PORTA to 0
        }
    }

    return 0;
}
