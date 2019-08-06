import freq_calc as NECD
import RPi.GPIO as gpio
import pigpio
from os import system


system("sudo pigpiod")
def freq():
    while(1):
            print('started')
            b = NECD.necd()
            pi = pigpio.pi()
            pin = 4
            b.init(pi,pin)
            b.enable()
            a = b._analyse_ir_pulses()
            pi.stop()
            if a == 1:
                result = b.freq()
                print(result)
                return result
                break

