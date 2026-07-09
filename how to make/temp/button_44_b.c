//  Code modified from Charles Holbrow website, How to Make (Almost) Anything, 2013.



#include <avr/io.h>

#define bit_get(byte,mask) ((byte) & (mask))
#define bit_set(byte,mask) ((byte) |= (mask))
#define bit_clear(byte,mask) ((byte) &= ~(mask))
#define BIT(x) (1 << (x))

  // Button  PA7 (pin 6).
  // LED     PB2 (pin 5).

int main()
{

  bit_set(PORTA,BIT(7));  // Turn button pull up resistor on by setting PA5(input) high
  bit_set(DDRB,BIT(2));   // Enable output on the LED pin (PB2)


  while (1)
  {
    if(bit_get(PINA,BIT(7)))  // Button is up, turn off
      bit_clear(PORTB,BIT(2));
    else                      // Button is down, turn on
      bit_set(PORTB,BIT(2));
  }
}
