#!/usr/bin/env python
#Author: Shriphani Palakodety
#Tool to aid those with noise cancellation headphones

#import the required modules
import pyaudio
import time
import VAD
import wave
import SkypeCallChecker
import sys
from os import name

#import Skype4Py move Skype specific part of code to new class

#variable that checks if Growl is installed. This is used for notifications.
Growl_exists = True

#try to import growl
try:
	import Growl
	
except ImportError:
	print "Growl is not installed.\n I will dump output in /var/tmp/audio.log\n"
	Growl_exists = False


#on unix machines, use /var/tmp/audio.log for the result.

if name == "posix":
    sys.stdout = open("/var/tmp/audio.log", "w")
else:
    sys.stdout = open("audio.log", "w")

skype_on_call = False
notifier = 0

#obtain a GrowlNotifier
if Growl_exists:
	notifier = Growl.GrowlNotifier('Listener',  ['Attention', 'test'])
	notifier.register()

def record():
    '''Records Input From Microphone Using PyAudio'''
    duration = 3 #record for 1 second. Pretty long duration don't you think
    outfile = "analysis.wav"
    
    p = pyaudio.PyAudio()
    
    inStream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,input=True, frames_per_buffer=1024)

    out = []
    upper_lim = 44100 / 1024 * duration #upper limit of the range we record to. 44100 / 1024 sized chunk * 5 seconds
    
    for i in xrange(0, upper_lim):
        data = inStream.read(1024)
        out.append(data)
    
    #now the writing section where we write to file
    data = ''.join(out)
    outFile = wave.open(outfile, "wb")
    outFile.setnchannels(1)
    outFile.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    outFile.setframerate(44100)
    outFile.writeframes(data)
    outFile.close()
    analyze()


def analyze():
    #run a VAD algorithm now
    speech =  VAD.Moattar_Homayounpour_VAD("analysis.wav", 3)
    #speech = VAD.Milanovic_Lukac_Domazetovic_VAD("analysis.wav")
    if speech:
        if Growl_exists:
	    notifier.notify('Attention','Listener', 'Speech Detected Nearby')
	else:
	    print "Speech Detected Nearby!\nSomeone might be calling you"
    else:
        print "Last call detected at " + time.strftime("%H:%M:%S on %b-%d", time.gmtime())
	
	
    
if __name__ == "__main__":
	record()
	skypeCallChecker = SkypeCallChecker.SkypeCallChecker()
	
	while True:
		if skypeCallChecker.__checkCallStatus__():
			#This essentially means that a call is taking place
			#Right now Skype4Py isn't working as intended and I
			#cannot fix it.
			print "\n"
			print "Skype Call In Progress"
			print "Listener On Hold"

			#Make the app sleep for 20 seconds
			time.sleep(20)
			
		else:   #Either Skype4Py is broken or there isn't a call
			record()
			time.sleep(2)
		
			


