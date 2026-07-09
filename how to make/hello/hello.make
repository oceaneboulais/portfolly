PROJECT=hello
SOURCES=$(PROJECT).c
MMCU=atxmega16e5
F_CPU = 32000000
TARGET = x16e5
PROGRAMMER= atmelice_pdi

CFLAGS=-mmcu=$(MMCU) -Wall -Os -DF_CPU=$(F_CPU)

$(PROJECT).hex: $(PROJECT).out
	avr-objcopy -O ihex $(PROJECT).out $(PROJECT).c.hex;\
	avr-size --mcu=$(MMCU) --format=avr $(PROJECT).out
 
$(PROJECT).out: $(SOURCES)
	avr-gcc $(CFLAGS) -I./ -o $(PROJECT).out $(SOURCES)
 
program: $(PROJECT).hex
	avrdude -p $(TARGET) -c $(PROGRAMMER) -U flash:w:$(PROJECT).c.hex
