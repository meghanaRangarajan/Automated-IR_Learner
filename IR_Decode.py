import Decoder as NECD
import RPi.GPIO as gpio
import pigpio
from os import system

p_id = None

system("sudo pigpiod")
b = NECD.necd()

def code(frequency):
    global p_id
    while(1):
            print('started')
            b = NECD.necd()
            i=0
            pi = pigpio.pi()
            print("______________________________________________PRESS_______________________________________________________________")
            pin = 4
            b.init(pi,pin)
            s = str(pi) + "    "+str(pin)
            #print(s)

            b.enable()
            a = b._analyse_ir_pulses(frequency)
            pi.stop()
            while(i<=30000):
                 i=i+1

            if a == 1:
                result = b.result_return()
                print(hex(result))
                p_id = b.return_protcol_id()
                print(p_id)
                return result
                break
def p():
    global p_id
    print("sfhdshf   ",p_id)
    return p_id

