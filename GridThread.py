import threading
import smbus #gives us a connection to the I2C bus
import time #for timing delays 
import random #random number generator 
import font0

class GridThread(threading.Thread):

	def ActivatePattern(self, pattern):
		self.pattern = pattern

	def ReverseBits (self,byte): 
		value = 0 
		currentBit = 7 
		for i in range(0,8): 
			if byte & (1<<i): 
				value |= (0x80>>i) 
				currentBit -= 1 
		return value  
	 
	def ROR (byte): 
		#perform a 'rotate right' command on byte 
		#bit 1 is rotated into bit 7; everything else shifted right 
		bit1 = byte & 0x01 #get right-most bit 
		byte >>= 1 #shift right 1 bit 
		if bit1: #was right-most bit a 1? 
			byte |= 0x80 #if so, rotate it into bit 7 
		return byte 
	 
	def ROL (byte): 
		#perform a 'rotate left' command on byte 
		#bit 7 is rotated into bit 1; everything else shifted left 
		bit7 = byte & 0x080 #get bit7 
		byte <<= 1 #shift left 1 bit 
		byte &= 0xFF #only keep 8 bits 
		if bit7: #was bit7 a 1? 
			byte |= 0x01 #if so, rotate it into bit 1 
		return byte 
	 
	 
	######################################################################## 
	# 
	# Lower Level LED Display routines. 
	# These write data directly to the Pi Matrix board 
	# 
	 
	def Write (self, register, value): 
		#Abstraction of I2C bus and the MCP23017 chip 
		#Call with the chip data register & value pair 
		#The chip address is constant ADDR (0x20). 
		self.bus.write_byte_data(self.ADDR,register,value) 
	 
	def EnableLEDS (self): 
		#Set up the 23017 for 16 output pins 
		self.Write(self.DIRA, 0x00) #all zeros = all outputs on PortA 
		self.Write(self.DIRB, 0x00) #all zeros = all outputs on PortB 
	 
	 
	def DisableLEDS (self): 
		#Set all outputs to high-impedance by making them inputs 
		self.Write(DIRA, 0xFF); #all ones = all inputs on PortA 
		self.Write(DIRB, 0xFF); #all ones = all inputs on PortB 
	 
	def TurnOffLEDS (): 
		#Clear the matrix display 
		Write(PORTA, 0x00) #set all columns low 
		Write(PORTB, 0x00) #set all rows low 
	 
	def TurnOnAllLEDS (): 
		#Turn on all 64 LEDs 
		Write(self.PORTA, 0xFF) #set all columns high 
		Write(self.PORTB, 0x00) #set all rows low 
	 
	def WriteToLED (self,rowPins,colPins): 
		#set logic state of LED matrix pins 
		self.Write(self.PORTA, 0x00) #turn off all columns; prevent ghosting  

		self.Write(self.PORTB, rowPins) #set rows first 
		self.Write(self.PORTA, colPins) #now turn on columns 
	 
	 
	######################################################################## 
	# 
	# More low-level routines, saved for learning purposes. 
	# 
	# 
	 
	def FastSetLED (row,col): 
	 	#turn on an individual LED at (row,col). All other LEDS off. 
		#ignores orientation. Unless speed is required, use SetLED instead 
		bus.write_byte_data(ADDR,PORTA,0x80>>col) 
		bus.write_byte_data(ADDR,PORTB,~(1<<row)) 
	 
	def FastSetColumn (col): 
		#turn on all LEDs in the specified column. Expects input of 0-7. 
		#ignores orientation. Unless speed is required, use SetColumn. 
		bus.write_byte_data(ADDR,PORTB,0x00) 
		bus.write_byte_data(ADDR,PORTA,0x80>>col) 
	 
	def FastSetRow (row): 
		#turn on all LEDs in the specified row. Expects input of 0-7. 
		#ignores orientation. Unless speed is required, use SetRow. 
		bus.write_byte_data(ADDR,PORTA,0xFF) 
		bus.write_byte_data(ADDR,PORTB,~(1<<row)) 
	 
	 
	######################################################################## 
	# 
	# Intermediate-level routines for 
	# LED Pixel, Row, Column, and Pattern display. 
	# Set constant ORIENTATION to 0,90,180,270 according to Matrix posn. 
	# 
	 
	def SetPattern (self, rowPattern,colPattern,orientation=180): 
		#Applies given row & column patterns to the matrix. 
		#For columns, bit 0 is left-most and bit 7 is at far right. 
		#For rows, bit 0 is at the top and bit 7 is at the bottom. 
		#Example: (0x07,0x03) will set 3 row bits & 2 columns bits, 
		#forming a rectagle of 6 lit LEDS in upper left corner of 
		#the matrix, three rows tall and two columns wide. 
		#Why? 0x07 = 0b00000111 (three lower row bits set). 
		# 0x03 = 0b00000011 (two lower column bits set). 


		global rows, columns #save current row/column 
		rows = rowPattern 
		columns = colPattern 

		if orientation==0: 
			WriteToLED(~rows,ReverseBits(columns)) 
		elif orientation==90: 
			WriteToLED(~columns,rows) 
		elif orientation==180: 
			self.WriteToLED(~self.ReverseBits(rows),columns)  

		elif orientation==270: 
			WriteToLED(~ReverseBits(columns),ReverseBits(rows)) 
	 
	 
	def SetLED(row,col): 
		#turn on an individual LED at (row,col). All other LEDS off. 
		#expects inputs of (0,0) to (7,7). 
		SetPattern(1<<row,1<<col) 
	 
	def SetColumn(col): 
		#turn on all LEDs in the specified column. Expects input of 0-7. 
		SetPattern(0xFF,1<<col)

	def SetRow(row): 
		#turn on all LEDs in the specified row. Expects input of 0-7. 
		SetPattern(1<<row,0xFF) 

	def MoveDown(): 
		#shifts entire display downward by one pixel 
		SetPattern(rows<<1,columns) 

	def MoveUp(): 
		#shifts entire display downward by one pixel 
		SetPattern(rows>>1,columns) 

	def MoveRight(): 
		#shifts entire display one pixel to the right 
		SetPattern(rows,columns<<1) 
	 
	def MoveLeft(): 
		#shifts entire display one pixel to the left 
		SetPattern(rows,columns>>1) 
 
	def MultiplexDisplay (self, z):  
		for row in range(0,8): 
			self.SetPattern(1<<row,z[row]) 
	 
	def RandomPatterns (numCycles=32):
	    delay = 0.05
	    for count in range(0,numCycles):
	        rowPattern = random.randint(0,255)
	        colPattern = random.randint(0,255)
	        SetPattern(rowPattern,colPattern)
	        time.sleep(delay)

	def ShowEyes ():
	    SetPattern(0x18,0x66)

	def RandomPixels (numCycles=128):
	    #puts random display patterns on the LED matrix
	    delay = 0.02
	    for count in range(0,numCycles):
	        row = random.randint(0,7)
	        col = random.randint(0,7)
	        SetLED (row,col)
	        time.sleep(delay)

	def BlinkEyes (numCycles=8,delay=0.5):
	    for count in range(0,numCycles):
	        ShowEyes()
	        time.sleep(delay)
	        TurnOffLEDS()
	        time.sleep(delay *0.2)

	def Blink (numCycles=8,delay=0.5):
	    #flashes current display off, then back on
	    for count in range(0,numCycles):
	        time.sleep(delay)
	        DisableLEDS()
	        time.sleep(delay)
	        EnableLEDS()

	def __init__(self, arg=None):
		super(GridThread,self).__init__()
		self._stop = False
		self.arg=arg

	def run (self):
		self.ADDR = 0x20 #The I2C address of our chip 
		self.DIRA = 0x00 #PortA I/O direction, by pin. 0=output, 1=input 
		self.DIRB = 0x01 #PortB I/O direction, by pin. 0=output, 1=input 
		self.PORTA = 0x12 #Register address for PortA 
		self.PORTB = 0x13 #Register address for PortB 
		self.ORIENTATION = 180 #default viewing angle for the pi & matrix 
		self.rows = 0x00 #starting pattern is (0,0) = all LEDS off 
		self.columns= 0x00 
		self.delay = 0.08 #time delay between LED display transitions 
		self.bus = smbus.SMBus(1) #initialize the I2 bus; use '0' for 

		self.EnableLEDS() #initialize the Pi Matrix board 
		self.pattern = [0x81,0x00,0x00,0x00,0x00,0x00,0x00,0x81]
		# start thread for text
		while not self._stop:
			self.MultiplexDisplay(self.pattern)

	def begin (self):
		self.start()
		return self

	def stop(self):
		self._stop = True

	def stopped(self):
		return self._stop == True

	def __enter__(self):
		print "woo"
		return self

	def __exit__(self, type, value, traceback):
		self._stop = True
		return isinstance(value, TypeError)
