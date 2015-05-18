import paho.mqtt.client as mqtt
import serial, time, json, os, inspect, re
from threading import Thread

if os.name == "posix":
    try:
        Serial = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)	# *nix
    except:
        Serial = serial.Serial("/dev/ttyACM0", 115200, timeout=0.1)	# *pi
else:
    Serial = serial.Serial("com4", 115200, rtscts=0)

Closing = False

def _find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

def on_connect(client, userdata, flags, rc):
	print("MQTT connected\r")
	client.subscribe("robot1/Cmd/#")
	
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload).strip() +"\r")
    Serial.write(str(msg.payload).strip() + "\n")

def ReadSerial():
    while Serial.isOpen() and not Closing:
        line = Serial.readline().strip()
        if line:
            print("com->" + line + "\r")
            client.publish("robot1",bytearray(line))

def OpenSerial():
    if Serial.isOpen():
        Serial.close()
    Serial.open()
    Thread(target=ReadSerial).start()

def CloseSerial():
    if Serial.isOpen():
        Serial.close()
        Thread(target=ReadSerial)._Thread__stop()

def GetChoice(choices):
    for i in xrange(len(choices)):
        print str(i + 1) + ")", choices[i]        
    k = int(getch()) - 1
    print choices[k]
    return k 

def RunMenu(menu):
    print(">> " + menu['!'])
    while True:
        for m in sorted(menu):
            if callable(menu[m]):
                print  m + ") " + menu[m].func_name
            elif type(menu[m]) is dict:
                print  m + ") " + menu[m]["!"]                
        print( "0) Exit")        
        k = getch()
        if k == '0':            
            return
        print
        if menu.has_key(k):
            if type(menu[k]) is dict:
                RunMenu(menu[k])
            else:
                if callable(menu[k]):
                    print menu[k].func_name
                    menu[k]()

def Exit():
    closing = True

MainMenu = {
    '!' : "Main",    
    }

# main

print("Spiked3.com python Serial <-> MQTT Bridge  ("),
print(str(Serial.port) + " )")

getch = _find_getch()

OpenSerial()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect_async("127.0.0.1")
client.loop_start()

RunMenu(MainMenu)
Closing = True

CloseSerial()
print "\nBye\n"
